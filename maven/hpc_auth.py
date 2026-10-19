"""In-app replacement for the old "check the terminal for a password prompt"
HPC SSH/Kerberos auth flow.

External tools (ssh, scp, rsync, conduit, klist) write interactive prompts
straight to whatever TTY launched the process. PTYCommandRunner spawns such
a command inside a pseudo-terminal it owns, so the prompt text lands in a
buffer this module controls instead of an arbitrary inherited terminal, and
the GUI can intercept and answer it.

This only works on POSIX (the pty module has no Windows implementation);
callers must fall back to the historical subprocess.run()-based behavior
on Windows.
"""
import dataclasses
import os
import pty
import re
import signal
import threading
import time
import types
from typing import Any, Callable, Literal

import streamlit as st

Status = Literal["idle", "running", "waiting_for_input", "done", "error"]
PromptKind = Literal["secret", "yes_no", "text"]

# Known interactive-prompt patterns, checked against the trailing slice of
# output seen so far. Order matters: more specific patterns first.
_PROMPT_PATTERNS: list[tuple[PromptKind, "re.Pattern[str]"]] = [
    ("yes_no", re.compile(r"(?i)are you sure you want to continue connecting \(yes/no(?:/\[fingerprint\])?\)\?\s*$")),
    ("yes_no", re.compile(r"(?i)\(yes/no\)\?\s*$")),
    ("secret", re.compile(r"(?im)^[^\n]*\bpassword:\s*$")),
    ("secret", re.compile(r"(?i)\[sudo\] password for [^:]+:\s*$")),
    ("secret", re.compile(r"(?i)\b(duo|mfa)\b[^\n]*(passcode|push|verification code)[^\n]*:\s*$")),
    ("secret", re.compile(r"(?i)verification code:\s*$")),
    ("secret", re.compile(r"(?i)enter pin[^\n]*:\s*$")),
    ("secret", re.compile(r"(?i)passphrase for key[^\n]*:\s*$")),
    ("secret", re.compile(r"(?i)password for [^\n@]+@[^\n]*:\s*$")),
]

# If no new output arrives for this long and the buffer doesn't end in a
# newline, treat the tail as an unrecognized prompt rather than hang forever
# on site-specific Kerberos/Duo PAM text that doesn't match a known pattern.
_IDLE_FALLBACK_SECONDS = 2.0

# How long a runner may sit in "waiting_for_input" before it's auto-cancelled.
_PROMPT_TIMEOUT_SECONDS = 300.0

_TAIL_SCAN_CHARS = 400


def _detect_prompt(buffer: str, last_activity: float) -> tuple[PromptKind, str] | None:
    tail = buffer[-_TAIL_SCAN_CHARS:]
    for kind, pattern in _PROMPT_PATTERNS:
        if pattern.search(tail):
            prompt_text = tail.strip().splitlines()[-1] if tail.strip() else ""
            return kind, prompt_text
    if tail and not tail.endswith("\n") and (time.monotonic() - last_activity) >= _IDLE_FALLBACK_SECONDS:
        prompt_text = tail.strip().splitlines()[-1] if tail.strip() else tail.strip()
        return "text", prompt_text
    return None


@dataclasses.dataclass
class CompletedPTYProcess:
    """subprocess.CompletedProcess-shaped result. A PTY merges stdout/stderr
    onto one stream, so both fields hold the same transcript - existing
    callers that substring-check `result.stderr` or `result.stdout` keep
    working unmodified."""
    returncode: int
    stdout: str
    stderr: str


class PTYCommandRunner:
    """Drives one external command inside a pseudo-terminal, incrementally,
    across Streamlit reruns. The Streamlit main thread only ever calls
    poll()/send_response()/cancel() - a single background reader thread
    owns the master fd."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.status: Status = "idle"
        self.output_buffer: str = ""
        self.returncode: int | None = None
        self.error: str | None = None
        self.prompt_kind: PromptKind | None = None
        self.pending_prompt_text: str | None = None
        self._master_fd: int | None = None
        self._pid: int | None = None
        self._last_activity: float = time.monotonic()
        self._reader_thread: threading.Thread | None = None

    def start(self, cmd: list[str], input_text: str | None = None, cwd: str | None = None) -> None:
        with self._lock:
            if self.status != "idle":
                raise RuntimeError("PTYCommandRunner.start() called more than once")
            self.status = "running"
            self._last_activity = time.monotonic()

        try:
            pid, master_fd = pty.fork()
        except OSError as exc:
            with self._lock:
                self.status = "error"
                self.error = f"Failed to spawn command: {exc}"
            return

        if pid == 0:
            # Child
            try:
                if cwd:
                    os.chdir(cwd)
                os.execvp(cmd[0], cmd)
            except Exception:
                os._exit(127)
        else:
            self._pid = pid
            self._master_fd = master_fd
            self._reader_thread = threading.Thread(
                target=self._read_loop, args=(input_text,), daemon=True
            )
            self._reader_thread.start()

    def _read_loop(self, input_text: str | None) -> None:
        assert self._master_fd is not None
        fd = self._master_fd
        if input_text:
            try:
                os.write(fd, input_text.encode("utf-8", errors="replace"))
                os.write(fd, b"\x04")  # EOF (Ctrl-D) so e.g. `python3 -` sees end of stdin
            except OSError:
                pass
        while True:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                chunk = b""
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            with self._lock:
                self.output_buffer += text
                self._last_activity = time.monotonic()
                if self.status == "running":
                    detected = _detect_prompt(self.output_buffer, self._last_activity)
                    if detected is not None:
                        self.prompt_kind, self.pending_prompt_text = detected
                        self.status = "waiting_for_input"
        self._finish()

    def _finish(self) -> None:
        assert self._pid is not None
        try:
            _, exit_status = os.waitpid(self._pid, 0)
            returncode = os.waitstatus_to_exitcode(exit_status)
        except ChildProcessError:
            returncode = -1
        try:
            os.close(self._master_fd)  # type: ignore[arg-type]
        except OSError:
            pass
        with self._lock:
            self.returncode = returncode
            self.status = "error" if returncode != 0 and self.error else "done"

    def poll(self) -> Status:
        with self._lock:
            if self.status == "waiting_for_input":
                if time.monotonic() - self._last_activity > _PROMPT_TIMEOUT_SECONDS:
                    self.error = "Timed out waiting for credentials input."
                    self._cancel_locked()
            return self.status

    def send_response(self, text: str) -> None:
        with self._lock:
            if self.status != "waiting_for_input" or self._master_fd is None:
                return
            try:
                os.write(self._master_fd, text.encode("utf-8", errors="replace") + b"\n")
            except OSError:
                pass
            self.status = "running"
            self.pending_prompt_text = None
            self.prompt_kind = None
            self._last_activity = time.monotonic()

    def cancel(self) -> None:
        with self._lock:
            self._cancel_locked()

    def _cancel_locked(self) -> None:
        if self._pid is not None and self.status in ("running", "waiting_for_input"):
            try:
                os.killpg(os.getpgid(self._pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    os.kill(self._pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError, OSError):
                    pass
            self.status = "error"
            self.error = self.error or "Cancelled by user."

    def run_blocking(self, cmd: list[str], timeout: float | None = None,
                      poll_interval: float = 0.2, registry_key: str | None = None) -> CompletedPTYProcess:
        """For use from a non-Streamlit thread (e.g. inside a monkeypatched
        dsi.sync call). Blocks the calling thread, publishing itself into
        ActivePromptRegistry whenever it needs GUI input, and waiting on
        an Event that send_response() (called from the Streamlit thread) sets."""
        self._answered_event = threading.Event()
        self.start(cmd)
        key = registry_key or f"sync_call_{id(self)}"
        start_time = time.monotonic()
        try:
            while True:
                status = self.poll()
                if status == "waiting_for_input":
                    self._answered_event.clear()
                    ActivePromptRegistry.publish(self, key)
                    self._answered_event.wait(timeout=poll_interval)
                    continue
                if status in ("done", "error"):
                    ActivePromptRegistry.clear(key)
                    break
                if timeout is not None and (time.monotonic() - start_time) > timeout:
                    ActivePromptRegistry.clear(key)
                    self.cancel()
                    import subprocess as _subprocess
                    raise _subprocess.TimeoutExpired(cmd, timeout)
                time.sleep(poll_interval)
        finally:
            ActivePromptRegistry.clear(key)

        if self.status == "error" and self.returncode is None:
            raise RuntimeError(self.error or "Command failed to run")
        return CompletedPTYProcess(
            returncode=self.returncode if self.returncode is not None else 1,
            stdout=self.output_buffer,
            stderr=self.output_buffer,
        )

    def send_response_threadsafe(self, text: str) -> None:
        """Like send_response, but also wakes a thread blocked in run_blocking()."""
        self.send_response(text)
        event = getattr(self, "_answered_event", None)
        if event is not None:
            event.set()


class ActivePromptRegistry:
    """Process-wide single slot: whichever runner currently needs GUI input
    publishes itself here, so Streamlit's polling fragment has exactly one
    place to look regardless of whether that runner is driven directly or
    nested inside a background thread running a dsi.sync.Sync call."""
    _lock = threading.Lock()
    _current: tuple[str, PTYCommandRunner] | None = None

    @classmethod
    def publish(cls, runner: PTYCommandRunner, key: str) -> None:
        with cls._lock:
            cls._current = (key, runner)

    @classmethod
    def current(cls) -> tuple[str, PTYCommandRunner] | None:
        with cls._lock:
            return cls._current

    @classmethod
    def clear(cls, key: str) -> None:
        with cls._lock:
            if cls._current is not None and cls._current[0] == key:
                cls._current = None


def _session_key(key: str) -> str:
    return f"_pty_runner_{key}"


def run_ssh_step(key: str, cmd: list[str], title: str,
                  input_text: str | None = None) -> CompletedPTYProcess | None:
    """Streamlit-aware helper: runs `cmd` inside a PTY, surfacing any
    interactive prompt as an in-app dialog instead of a terminal prompt.

    Returns None while the command is still in flight (the caller must
    `st.stop()` immediately), or the CompletedPTYProcess once it's done."""
    state_key = _session_key(key)
    runner: PTYCommandRunner | None = st.session_state.get(state_key)
    if runner is None:
        runner = PTYCommandRunner()
        runner.start(cmd, input_text=input_text)
        st.session_state[state_key] = runner

    status = runner.poll()
    if status in ("running", "waiting_for_input"):
        _render_pty_fragment(state_key, title)
        return None

    del st.session_state[state_key]
    if status == "error" and runner.returncode is None:
        return CompletedPTYProcess(returncode=1, stdout=runner.output_buffer,
                                    stderr=f"{runner.error}\n{runner.output_buffer}")
    return CompletedPTYProcess(returncode=runner.returncode if runner.returncode is not None else 1,
                                stdout=runner.output_buffer, stderr=runner.output_buffer)


def cancel_ssh_step(key: str) -> None:
    """Cancel and clean up a runner started by run_ssh_step, if one is
    still in flight. Call this before resetting session state that would
    otherwise orphan a live subprocess (e.g. navigating back a screen)."""
    state_key = _session_key(key)
    runner: PTYCommandRunner | None = st.session_state.pop(state_key, None)
    if runner is not None:
        runner.cancel()


def cancel_sync_call(key: str) -> None:
    """Cancel and clean up a background call started by
    run_sync_call_with_gui_auth, if one is still in flight. Cancels whatever
    PTY subprocess it's currently waiting on (which causes the wrapped
    function to raise and the background thread to exit promptly), then
    drops the handle so the UI stops polling it."""
    state_key = f"_sync_call_{key}"
    handle: _SyncCallHandle | None = st.session_state.pop(state_key, None)
    if handle is None:
        return
    current = ActivePromptRegistry.current()
    if current is not None and current[0].startswith(f"sync_call_{key}"):
        _, runner = current
        runner.cancel()


@st.fragment(run_every="0.5s")
def _render_pty_fragment(state_key: str, title: str) -> None:
    runner: PTYCommandRunner | None = st.session_state.get(state_key)
    if runner is None:
        return
    status = runner.poll()
    if status == "waiting_for_input":
        _password_dialog(state_key, title)
    elif status in ("done", "error"):
        st.rerun()
    else:
        st.info(f"{title} — connecting...")


@st.dialog("Credentials Needed", width="medium", dismissible=False)
def _password_dialog(state_key: str, title: str) -> None:
    runner: PTYCommandRunner | None = st.session_state.get(state_key)
    if runner is None:
        return
    st.write(title)
    st.caption(runner.pending_prompt_text or "Input requested")

    if runner.prompt_kind == "yes_no":
        y_col, n_col = st.columns(2)
        with y_col:
            if st.button("Yes", type="primary", width="stretch", key=f"{state_key}_yes"):
                runner.send_response_threadsafe("yes")
                st.rerun()
        with n_col:
            if st.button("No", width="stretch", key=f"{state_key}_no"):
                runner.send_response_threadsafe("no")
                st.rerun()
    else:
        masked = runner.prompt_kind == "secret"
        value = st.text_input("Response", type="password" if masked else "default",
                               key=f"{state_key}_input")
        if st.button("Submit", type="primary", width="stretch", key=f"{state_key}_submit"):
            runner.send_response_threadsafe(value)
            st.rerun()

    if st.button("Cancel", width="stretch", key=f"{state_key}_cancel"):
        runner.cancel()
        st.rerun()


@dataclasses.dataclass
class _SyncCallHandle:
    thread: threading.Thread
    done: bool = False
    error: Exception | None = None


def run_sync_call_with_gui_auth(key: str, func: Callable[[], Any], title: str) -> tuple[bool, Exception | None] | None:
    """For call sites that invoke dsi.sync.Sync methods directly (rather
    than a raw ssh command). Runs `func()` on a background thread so any
    nested PTY prompt triggered inside it (via the monkeypatched
    subprocess.run) can be surfaced through the same dialog machinery as
    run_ssh_step, without blocking Streamlit's own thread.

    Returns None while in flight (caller must st.stop()), or
    (True, None) / (False, exception) once finished."""
    state_key = f"_sync_call_{key}"
    handle: _SyncCallHandle | None = st.session_state.get(state_key)

    if handle is None:
        def _runner() -> None:
            try:
                func()
            except Exception as exc:  # noqa: BLE001 - surfaced to caller, not swallowed
                handle.error = exc
            finally:
                handle.done = True

        thread = threading.Thread(target=_runner, daemon=True)
        handle = _SyncCallHandle(thread=thread)
        st.session_state[state_key] = handle
        thread.start()

    if not handle.done:
        current = ActivePromptRegistry.current()
        if current is not None and current[0].startswith(f"sync_call_{key}"):
            _, runner = current
            if runner.poll() == "waiting_for_input":
                _sync_password_dialog(state_key, title, runner)
        else:
            _render_sync_waiting_fragment(state_key, title)
        return None

    del st.session_state[state_key]
    return (handle.error is None, handle.error)


@st.fragment(run_every="0.5s")
def _render_sync_waiting_fragment(state_key: str, title: str) -> None:
    handle: _SyncCallHandle | None = st.session_state.get(state_key)
    if handle is None:
        return
    if handle.done:
        st.rerun()
    else:
        st.info(f"{title} — working...")


@st.dialog("Credentials Needed", width="medium", dismissible=False)
def _sync_password_dialog(state_key: str, title: str, runner: PTYCommandRunner) -> None:
    st.write(title)
    st.caption(runner.pending_prompt_text or "Input requested")

    if runner.prompt_kind == "yes_no":
        y_col, n_col = st.columns(2)
        with y_col:
            if st.button("Yes", type="primary", width="stretch", key=f"{state_key}_yes"):
                runner.send_response_threadsafe("yes")
                st.rerun()
        with n_col:
            if st.button("No", width="stretch", key=f"{state_key}_no"):
                runner.send_response_threadsafe("no")
                st.rerun()
    else:
        masked = runner.prompt_kind == "secret"
        value = st.text_input("Response", type="password" if masked else "default",
                               key=f"{state_key}_input")
        if st.button("Submit", type="primary", width="stretch", key=f"{state_key}_submit"):
            runner.send_response_threadsafe(value)
            st.rerun()


def install_dsi_pty_patches(sync_module: Any, sync_cls: type) -> None:
    """Monkeypatch dsi.sync's subprocess usage so every scp/rsync/conduit/
    klist call it makes internally routes through a PTY, same as app.py's
    own ssh calls. Installed once at import time, before any Sync(...) is
    constructed.

    dsi-workflow is a third-party pip dependency we don't own, so this
    patches it at runtime rather than forking it. If a future dsi-workflow
    release restructures sync.py, fail loudly here rather than silently
    leaving the terminal-prompt behavior in place.
    """
    if not hasattr(sync_cls, "execute_cmd"):
        raise RuntimeError(
            "dsi.sync.Sync.execute_cmd not found - dsi-workflow's internals "
            "changed and the HPC auth GUI patch needs updating."
        )

    def _pty_subprocess_run(cmd: Any, **kwargs: Any) -> CompletedPTYProcess:
        if kwargs.get("shell"):
            executable = kwargs.get("executable") or "/bin/sh"
            command = [executable, "-c", cmd if isinstance(cmd, str) else " ".join(cmd)]
        else:
            command = list(cmd)
        timeout = kwargs.get("timeout")
        runner = PTYCommandRunner()
        return runner.run_blocking(command, timeout=timeout)

    def _pty_execute_cmd(self: Any, cmd: list[str], cmd_name: str, timer: bool = False) -> str:
        result = _pty_subprocess_run(cmd)
        if result.returncode != 0:
            lowered = result.stderr.lower()
            if "too many authentication failures" in lowered:
                raise RuntimeError(
                    f"{cmd_name} failed due to multiple incorrect password attempts. "
                    "Check the password and remote path."
                ) from None
            if "no credentials" in lowered:
                raise RuntimeError(
                    "Kerberos authentication error: No credentials found. Please "
                    f"type 'conduit get' to issue a ticket.\nKerberos message: {result.stderr}"
                ) from None
            raise RuntimeError(f"{cmd_name} failed: \n{result.stderr}") from None
        return result.stdout

    # sync_module.subprocess is the *same* module object as the global
    # `subprocess` module (sys.modules["subprocess"]) - assigning .run on it
    # directly would patch subprocess.run/check_output for every other
    # importer in the process too (e.g. matplotlib's fontconfig lookup,
    # which then chokes on a str where it expects bytes). Rebind
    # sync_module.subprocess to a shim object instead, leaving the real
    # subprocess module untouched for everyone else.
    shim_attrs = {
        name: getattr(sync_module.subprocess, name)
        for name in dir(sync_module.subprocess) if not name.startswith("_")
    }
    shim_attrs["run"] = _pty_subprocess_run
    sync_module.subprocess = types.SimpleNamespace(**shim_attrs)
    sync_cls.execute_cmd = _pty_execute_cmd
