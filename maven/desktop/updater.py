"""Update-check logic: checks GitHub Releases on the public lanl/maven repo
and, if a newer version exists, prompts the user to update rather than
silently replacing the running binary. Once a release has been out for
longer than UPDATE_GRACE_PERIOD_DAYS, the prompt becomes mandatory (no
"Later" option).

Updating always installs the platform installer artifact (.dmg /
installer.exe / .AppImage) the same way a fresh install would -- this repo
never overwrites a running, possibly-signed binary in place.

The repo is public, so the Releases API is read anonymously -- there is no
embedded credential here (unlike a private-repo variant of this pattern).

Every check (startup or manual) is logged to the shared wrapper log
(<data_dir>/wrapper.log, see maven/desktop/wrapper_log.py), since the
packaged --windowed build has no visible stdout/stderr.

HTTPS requests are verified against the OS trust store (via `truststore`)
rather than the `certifi` bundle `requests` ships with. On machines behind
a TLS-inspecting proxy (e.g. LANL's Zscaler), the OS already trusts the
proxy's root CA -- certifi's public CA list doesn't, which otherwise makes
every HTTPS call fail with SSLCertVerificationError. This mirrors the same
truststore injection maven/app.py does via ursa.util.http.inject_truststore_into_ssl();
it's intentionally invoked here too since updater.py's startup check can run
before app.py is ever imported. This must never be "fixed" by
bundling/exporting a cert from any particular machine into this repo;
relying on the OS trust store is what makes it work on any machine.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from datetime import datetime, timedelta, timezone
from tkinter import messagebox

import truststore

truststore.inject_into_ssl()

import requests
from packaging.version import InvalidVersion, Version

from maven._version import __version__
from maven.desktop.paths import get_data_dir
from maven.desktop.wrapper_log import get_logger

GITHUB_REPO = "lanl/maven"

API_URL = "https://api.github.com/repos/{repo}/releases"

UPDATE_GRACE_PERIOD_DAYS = 7

PLATFORM_ASSET_NAMES = {
    "win32": "maven-windows-installer.exe",
    "darwin": "maven-macos-installer.dmg",
    "linux": "maven-linux-installer.AppImage",
}

UPDATE_MARKER_FILENAME = "pending_update_from.txt"
UPDATE_FAILURE_MARKER_FILENAME = "failed_update.txt"
INSTALL_TRACE_LOG_FILENAME = "install_trace.log"

logger = get_logger("updater")

# Guards check_and_apply_update (startup, main thread) and run_manual_check
# ("Check for Updates" menu item, a pywebview-managed background thread --
# and the thread that dispatches menu actions isn't reused, so clicking the
# menu item again while a check/install is still running starts a second,
# fully independent run of this same code). Without this, two installs can
# race: both write to the same fixed /tmp script paths (see _install_macos)
# and both call AppleScript's administrator-privileges prompt independently,
# producing two password prompts and two concurrent Contents-swap attempts
# against the same .app bundle -- which is what corrupts the install and
# leaves the app unable to reopen. A non-blocking acquire is used so a
# second trigger is rejected immediately rather than queued, since queueing
# would just delay the same race rather than prevent it.
_update_lock = threading.Lock()


def get_latest_release():
    """Returns the release with the highest semantic version, not GitHub's
    notion of "latest" (/releases/latest returns the most recently
    *published* release, which silently goes stale/wrong whenever an older
    tag gets deleted and re-published, e.g. to ship a fix on top of it)."""
    url = API_URL.format(repo=GITHUB_REPO)
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    releases = response.json()

    candidates = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        try:
            version = Version(release["tag_name"].lstrip("v"))
        except InvalidVersion:
            continue
        candidates.append((version, release))

    if not candidates:
        raise RuntimeError(f"no usable releases found for {GITHUB_REPO!r}")
    return max(candidates, key=lambda pair: pair[0])[1]


def is_newer(release):
    remote_version = release["tag_name"].lstrip("v")
    return Version(remote_version) > Version(__version__)


def update_deadline(release):
    published_at = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
    return published_at + timedelta(days=UPDATE_GRACE_PERIOD_DAYS)


def find_asset_url(release):
    asset_name = PLATFORM_ASSET_NAMES.get(sys.platform)
    if asset_name is None:
        return None
    for asset in release.get("assets", []):
        if asset["name"] == asset_name:
            return asset["url"]
    return None


def download_asset(asset_url, dest_path):
    headers = {"Accept": "application/octet-stream"}
    response = requests.get(asset_url, headers=headers, stream=True, timeout=30)
    with response:
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)


def _update_marker_path():
    return get_data_dir() / UPDATE_MARKER_FILENAME


def _update_failure_marker_path():
    return get_data_dir() / UPDATE_FAILURE_MARKER_FILENAME


def _install_trace_log_path():
    """Plain-text, append-only log written to directly by the detached
    install shell scripts (both the unprivileged outer script and the
    privileged inner one) as they run -- unlike wrapper.log, which only
    Python writes to. The scripts run after this process has already called
    os._exit(0), so there's no other way to see what they actually did step
    by step if something between the file swap and the final relaunch goes
    wrong without tripping any of the existing failure-marker checks."""
    return get_data_dir() / INSTALL_TRACE_LOG_FILENAME


def write_update_marker(from_version):
    """Records the version we're updating *from*, read back on the next
    launch (post-install) to show a "successfully updated" message."""
    _update_marker_path().write_text(from_version)


def consume_update_marker():
    """Returns the previous version if this launch follows an update
    install, deleting the marker so the message only shows once."""
    marker_path = _update_marker_path()
    if not marker_path.exists():
        return None
    from_version = marker_path.read_text().strip()
    marker_path.unlink()
    return from_version or None


def write_update_failure_marker(reason):
    """Records why an install attempt failed, read back on the next launch
    to tell the user the automatic update didn't complete. Called from the
    detached install scripts (which run after this process has already
    exited), not from Python, so this must be callable with a plain string
    reason and nothing else."""
    _update_failure_marker_path().write_text(reason)


def consume_update_failure_marker():
    """Returns the failure reason if the previous install attempt failed,
    deleting the marker so the message only shows once."""
    marker_path = _update_failure_marker_path()
    if not marker_path.exists():
        return None
    reason = marker_path.read_text().strip()
    marker_path.unlink()
    return reason or None


def show_update_complete_dialog(from_version, to_version, parent=None):
    owns_root = parent is None
    root = parent if parent is not None else tk.Tk()
    if owns_root:
        root.withdraw()
    messagebox.showinfo(
        "Update complete",
        f"MAVEN was updated from v{from_version} to v{to_version}.",
        master=root,
    )
    if owns_root:
        root.destroy()


def show_update_failed_dialog(reason, parent=None):
    owns_root = parent is None
    root = parent if parent is not None else tk.Tk()
    if owns_root:
        root.withdraw()
    messagebox.showwarning(
        "Update failed",
        f"MAVEN could not finish updating and is still running v{__version__}.\n\nDetails: {reason}",
        master=root,
    )
    if owns_root:
        root.destroy()


def show_updating_dialog(message="Application updating...", parent=None):
    """Non-blocking "please wait" window shown while a download/install is
    in progress. The process calls os._exit() once the platform installer
    script is handed off, so this window is torn down with the process --
    nothing needs to explicitly close it."""
    root = tk.Toplevel(parent) if parent is not None else tk.Tk()
    root.title("MAVEN")
    root.resizable(False, False)
    tk.Label(root, text=message, padx=30, pady=20).pack()
    root.tk.eval(f"tk::PlaceWindow {root} center")
    root.update()
    return root


def prompt_update_dialog(current_version, remote_version, deadline, mandatory, parent=None):
    """Shows a blocking dialog and returns "update", "later", or "quit"."""
    result = {"choice": "quit" if mandatory else "later"}

    root = tk.Toplevel(parent) if parent is not None else tk.Tk()
    root.title("Update available")
    root.resizable(False, False)

    deadline_str = deadline.astimezone().strftime("%Y-%m-%d %H:%M")
    lines = [f"A new version is available: v{remote_version} (you have v{current_version})."]
    if mandatory:
        lines.append("This update is required to continue.")
    else:
        lines.append(f"Updates become mandatory on {deadline_str}.")
    message = "\n".join(lines)

    tk.Label(root, text=message, justify="left", padx=20, pady=20).pack()

    button_frame = tk.Frame(root, pady=10)
    button_frame.pack()

    def choose(choice):
        result["choice"] = choice
        root.destroy()

    tk.Button(button_frame, text="Update Now", width=12, command=lambda: choose("update")).pack(
        side="left", padx=5
    )
    if mandatory:
        tk.Button(button_frame, text="Quit", width=12, command=lambda: choose("quit")).pack(
            side="left", padx=5
        )
        root.protocol("WM_DELETE_WINDOW", lambda: choose("quit"))
    else:
        tk.Button(button_frame, text="Later", width=12, command=lambda: choose("later")).pack(
            side="left", padx=5
        )
        root.protocol("WM_DELETE_WINDOW", lambda: choose("later"))

    root.tk.eval(f"tk::PlaceWindow {root} center")
    if parent is not None:
        parent.wait_window(root)
    else:
        root.mainloop()

    return result["choice"]


def _write_and_launch(script_path, script_body, launch_cmd):
    with open(script_path, "w") as f:
        f.write(script_body)
    os.chmod(script_path, 0o755)
    subprocess.Popen(launch_cmd, close_fds=True, start_new_session=True)


def _as_escape(text):
    """Escapes a string for embedding inside a double-quoted AppleScript
    string literal (backslash and double-quote are the only characters
    AppleScript string literals treat specially)."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _install_macos(installer_path, current_exe):
    """Swaps the app bundle's Contents/ directory in place rather than
    deleting and recreating the .app directory itself. macOS's App
    Management protection blocks `rm -rf` (and `mv`) on a registered .app
    bundle's own directory entry in /Applications even when the owning user
    can freely create/delete every file *inside* it -- so this stages the
    new build alongside the old one (Contents.new), then does two same-
    volume renames (Contents -> Contents.old, Contents.new -> Contents),
    which are themselves just moving directories owned by the user *inside*
    the still-existing bundle, not touching the bundle's own entry. Every
    step is checked so that a failure rolls back to a launchable bundle
    (old or new) instead of silently leaving a half-swapped Contents/ that
    won't open.

    Some managed Mac deployments install the app somewhere the signed-in
    user can't write to at all (e.g. owned by a different admin account),
    so the swap above fails outright with a permission error. Rather than
    trying unprivileged first, this always asks for administrator
    credentials up front via AppleScript's `do shell script ... with
    administrator privileges`, which pops the native macOS password dialog.
    The actual swap/verify/rollback logic runs as its own script (`inner`)
    so the whole chain -- including every rollback branch -- executes under
    one elevated session; splitting it across multiple `do shell script`
    calls would risk a second password prompt mid-rollback, or a rollback
    step that can no longer write into a bundle a previous privileged step
    already modified. Mounting/unmounting the downloaded .dmg and deleting
    user-owned temp files don't need root, so those stay in the outer,
    unprivileged script. The AppleScript source itself is written to its
    own file (rather than inlined as a `osascript -e '...'` argument) to
    avoid nesting an AppleScript string literal inside a POSIX-shell single-
    quoted argument, which have no mutually-safe escaping for each other's
    quote characters.

    The inner (privileged) script must never call `open` on the bundle --
    `open` run as root can't hand the GUI launch off to the logged-in user's
    window server session, so the relaunched app would never actually show a
    window (dock icon just bounces forever). The inner script only verifies
    the swapped-in executable exists and is executable; the outer
    (unprivileged) script does the real `open`, after the privileged step
    finishes either way."""
    # current_exe is .../MAVEN.app/Contents/MacOS/maven-macos
    app_bundle = os.path.dirname(os.path.dirname(os.path.dirname(current_exe)))
    bundle_name = os.path.basename(app_bundle)
    mount_point = tempfile.mkdtemp(prefix="maven-update-")
    pid = os.getpid()
    # e.g. "MacOS/maven-macos", used to sanity-check a swapped-in Contents/
    # without ever launching the app as root (see note below).
    exe_rel_path = os.path.relpath(current_exe, os.path.join(app_bundle, "Contents"))

    q_bundle = _sh_quote(app_bundle)
    q_mount = _sh_quote(mount_point)
    q_installer = _sh_quote(installer_path)
    q_fail_marker = _sh_quote(str(_update_failure_marker_path()))
    q_trace_log = _sh_quote(str(_install_trace_log_path()))
    new_contents = os.path.join(app_bundle, "Contents.new")
    old_contents = os.path.join(app_bundle, "Contents.old")
    live_contents = os.path.join(app_bundle, "Contents")
    q_new = _sh_quote(new_contents)
    q_old = _sh_quote(old_contents)
    q_live = _sh_quote(live_contents)
    q_live_exe = _sh_quote(os.path.join(live_contents, exe_rel_path))
    q_exe_name = _sh_quote(os.path.basename(exe_rel_path))

    # Suffixed with the current pid so an overlapping install (e.g. two
    # update triggers racing before _update_lock existed, or two separate
    # app instances) can't stomp on another install's in-flight script
    # files out from under it.
    inner_script_path = os.path.join(tempfile.gettempdir(), f"maven_update_inner_{pid}.sh")
    applescript_path = os.path.join(tempfile.gettempdir(), f"maven_update_{pid}.applescript")
    q_inner = _sh_quote(inner_script_path)
    q_applescript = _sh_quote(applescript_path)

    # Note: this script runs "with administrator privileges" (as root), so it
    # must never call `open` on the app bundle -- `open` run as root can't
    # hand the GUI launch off to the logged-in user's window server session,
    # so Launch Services just queues the request forever (dock icon bounces,
    # no window ever appears). Instead this only verifies the swapped-in
    # executable exists and is executable; the actual `open` happens later in
    # the unprivileged outer script, running as the real logged-in user.
    inner_script_body = f"""#!/bin/sh
trace() {{
    echo "$(date '+%Y-%m-%d %H:%M:%S') [inner pid {pid}] $1" >> {q_trace_log}
}}
write_failure() {{
    echo "$1" > {q_fail_marker}
    trace "FAILURE: $1"
}}

trace "inner script start, whoami=$(whoami)"

rm -rf {q_new}
if ! cp -R {q_mount}/{_sh_quote(bundle_name)}/Contents {q_new}; then
    write_failure "failed to copy the new application files"
    rm -rf {q_new}
    exit 1
fi
trace "staged new Contents.new"

rm -rf {q_old}
if ! mv {q_live} {q_old}; then
    write_failure "failed to set aside the previous application files"
    rm -rf {q_new}
    exit 1
fi
trace "moved live Contents to Contents.old"

if ! mv {q_new} {q_live}; then
    write_failure "failed to install the new application files"
    mv {q_old} {q_live}
    exit 1
fi
trace "moved Contents.new into place as live Contents"

if [ ! -x {q_live_exe} ]; then
    write_failure "updated application files are not launchable, reverted to the previous version"
    rm -rf {q_live}
    mv {q_old} {q_live}
    exit 1
fi
trace "verified swapped-in executable is launchable"

rm -rf {q_old}
trace "inner script end, swap succeeded"
"""
    with open(inner_script_path, "w") as f:
        f.write(inner_script_body)
    os.chmod(inner_script_path, 0o755)

    applescript_body = (
        f'do shell script "{_as_escape(inner_script_path)}" '
        "with administrator privileges "
        'with prompt "MAVEN needs administrator access to install the update."'
    )
    with open(applescript_path, "w") as f:
        f.write(applescript_body)

    script_path = os.path.join(tempfile.gettempdir(), f"maven_update_{pid}.sh")
    script_body = f"""#!/bin/sh
trace() {{
    echo "$(date '+%Y-%m-%d %H:%M:%S') [outer pid {pid}] $1" >> {q_trace_log}
}}
write_failure() {{
    echo "$1" > {q_fail_marker}
    trace "FAILURE: $1"
}}

trace "outer script start, waiting for pid {pid} to exit"
while kill -0 {pid} 2>/dev/null; do sleep 0.5; done
trace "pid {pid} has exited"

if ! hdiutil attach {q_installer} -mountpoint {q_mount} -nobrowse -quiet; then
    write_failure "failed to mount the downloaded update image"
    open -n {q_bundle}
    rm -f {q_inner} {q_applescript} "$0"
    exit 1
fi
trace "mounted installer image at {mount_point}"

if ! osascript {q_applescript}; then
    if [ ! -f {q_fail_marker} ]; then
        write_failure "administrator authorization was not granted"
    fi
fi
trace "osascript (privileged inner script) finished"

# The privileged inner script never calls `open` itself (root can't hand a
# GUI launch off to the logged-in user's window server session, so the app
# would never actually appear) -- it only swaps files and leaves a failure
# marker if the swap didn't produce a launchable bundle. This script runs
# unprivileged as the real logged-in user, so it does the actual launch,
# either way, once the privileged step above has finished.
#
# -n forces a new process instead of plain `open`'s default of activating
# an already-running instance. Harmless either way since the old process
# has already exited, but removes any dependency on exactly how quickly
# LaunchServices notices that exit.
trace "calling open -n on the bundle, whoami=$(whoami)"
open -n {q_bundle}
trace "open -n exit code: $?"

# open -n returning 0 only means LaunchServices accepted the request, not
# that the process actually came up and stayed alive -- a silent kill before
# Python logging initializes (e.g. Gatekeeper rejecting an ad-hoc-signed
# binary) leaves no trace anywhere else. This distinguishes that case from
# one where the process starts but dies even earlier than wrapper.log.
sleep 2
if pgrep -f {q_exe_name} >/dev/null 2>&1; then
    trace "relaunched process is alive 2s after open -n"
else
    trace "relaunched process is NOT running 2s after open -n"
fi

hdiutil detach {q_mount} -quiet
rm -f {q_installer} {q_inner} {q_applescript} "$0"
trace "outer script end"
"""
    _write_and_launch(script_path, script_body, ["/bin/sh", script_path])
    os._exit(0)


def _install_windows(installer_path, current_exe):
    """Runs the NSIS installer silently, then relaunches. If the installer
    itself reports failure (nonzero exit code), the failure marker is
    written and the *current* exe is relaunched as a fallback instead of
    the (possibly not actually installed) new one, so a failed update still
    leaves a working app running."""
    pid = os.getpid()
    fail_marker = str(_update_failure_marker_path())

    script_path = os.path.join(tempfile.gettempdir(), f"maven_update_{pid}.bat")
    script_body = (
        "@echo off\r\n"
        f":wait\r\n"
        f'tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL\r\n'
        f"if not errorlevel 1 (\r\n"
        f"  ping 127.0.0.1 -n 2 > nul\r\n"
        f"  goto wait\r\n"
        f")\r\n"
        f'"{installer_path}" /S\r\n'
        f"if errorlevel 1 (\r\n"
        f'  echo installer exited with a non-zero status> "{fail_marker}"\r\n'
        f'  start "" "{current_exe}"\r\n'
        f'  del "{installer_path}"\r\n'
        f'  del "%~f0"\r\n'
        f"  exit /b 1\r\n"
        f")\r\n"
        f'start "" "{current_exe}"\r\n'
        f'del "{installer_path}"\r\n'
        f'del "%~f0"\r\n'
    )
    DETACHED_PROCESS = 0x00000008
    with open(script_path, "w") as f:
        f.write(script_body)
    subprocess.Popen(
        ["cmd", "/c", script_path],
        creationflags=DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    os._exit(0)


def _install_linux(installer_path, current_exe):
    """Swaps the downloaded AppImage over the current one. If chmod or the
    move itself fails, the failure marker is written and whatever is still
    at `target` (the old build, since a failed mv doesn't touch it) is
    relaunched as a fallback."""
    target = os.environ.get("APPIMAGE") or current_exe
    pid = os.getpid()
    q_installer = _sh_quote(installer_path)
    q_target = _sh_quote(target)
    q_fail_marker = _sh_quote(str(_update_failure_marker_path()))

    script_path = os.path.join(tempfile.gettempdir(), f"maven_update_{pid}.sh")
    script_body = f"""#!/bin/sh
while kill -0 {pid} 2>/dev/null; do sleep 0.5; done

if ! chmod +x {q_installer}; then
    echo "failed to prepare the downloaded update" > {q_fail_marker}
    {q_target} &
    rm -f "$0"
    exit 1
fi

if ! mv {q_installer} {q_target}; then
    echo "failed to install the new application files" > {q_fail_marker}
    {q_target} &
    rm -f "$0"
    exit 1
fi

{q_target} &
rm -f "$0"
"""
    _write_and_launch(script_path, script_body, ["/bin/sh", script_path])
    os._exit(0)


def _sh_quote(path):
    return "'" + path.replace("'", "'\\''") + "'"


def install(installer_path):
    current_exe = os.environ.get("APPIMAGE") or sys.executable
    if sys.platform == "win32":
        _install_windows(installer_path, current_exe)
    elif sys.platform == "darwin":
        _install_macos(installer_path, current_exe)
    else:
        _install_linux(installer_path, current_exe)


def check_and_apply_update(splash=None):
    """Entry point called from desktop_main.py on startup. Best-effort: a
    failed *check* (offline, rate-limited) is swallowed so the app still
    launches normally. A failed *install* only blocks startup if the update
    had already become mandatory.

    splash is hidden any time a dialog needs the user's attention, so the
    two tkinter windows never overlap, and shown again afterward if startup
    is going to continue (i.e. not on the mandatory-quit or install paths,
    which end the process)."""
    if not _update_lock.acquire(blocking=False):
        logger.info("Startup update check: an update is already in progress, skipping")
        return
    try:
        _check_and_apply_update_locked(splash)
    finally:
        _update_lock.release()


def _check_and_apply_update_locked(splash):
    logger.info("Startup update check: current version is %s", __version__)

    from_version = consume_update_marker()
    if from_version is not None:
        logger.info("Update completed: %s -> %s", from_version, __version__)
        if splash:
            splash.hide()
        show_update_complete_dialog(from_version, __version__, parent=splash.root if splash else None)
        if splash:
            splash.show()

    failure_reason = consume_update_failure_marker()
    if failure_reason is not None:
        logger.error("Previous update attempt failed: %s", failure_reason)
        if splash:
            splash.hide()
        show_update_failed_dialog(failure_reason, parent=splash.root if splash else None)
        if splash:
            splash.show()

    if not getattr(sys, "frozen", False):
        logger.info("Running from source, not a packaged exe; skipping update check")
        return  # running from source, not a packaged exe; nothing to install

    try:
        release = get_latest_release()
    except Exception as exc:
        logger.warning("Startup update check failed, continuing without update: %s", exc)
        return

    remote_version = release["tag_name"].lstrip("v")
    if not is_newer(release):
        logger.info("Startup update check: up to date (latest release is %s)", remote_version)
        return

    logger.info("Startup update check: newer release found: %s", remote_version)
    deadline = update_deadline(release)
    mandatory = datetime.now(timezone.utc) >= deadline

    if splash:
        splash.hide()
    choice = prompt_update_dialog(
        __version__, remote_version, deadline, mandatory, parent=splash.root if splash else None
    )
    logger.info("Startup update dialog choice: %s", choice)

    if choice == "later":
        if splash:
            splash.show()
        return
    if choice == "quit":
        sys.exit(0)

    updating_window = show_updating_dialog(parent=splash.root if splash else None)
    try:
        asset_url = find_asset_url(release)
        if asset_url is None:
            raise RuntimeError(f"no release asset for platform {sys.platform!r}")
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        download_asset(asset_url, tmp_path)
        logger.info("Downloaded update asset, installing %s", remote_version)
        write_update_marker(__version__)
        install(tmp_path)  # dispatches to the platform installer, then exits
    except Exception as exc:
        logger.error("Startup update install failed: %s", exc)
        updating_window.destroy()
        if mandatory:
            sys.exit(1)
        if splash:
            splash.show()


_OVERLAY_ELEMENT_ID = "maven-update-overlay"


def _set_status(window, message):
    """Shows (or updates) a full-window overlay over the loaded page so the
    user sees that something is happening, instead of the window just
    appearing to hang while a check/download/install runs on the background
    thread pywebview dispatches menu actions on. `evaluate_js` is one of the
    few `window` methods documented as safe to call off the main thread
    (every backend marshals it onto its own UI thread/loop internally), so
    this is used instead of trying to touch tkinter from here."""
    logger.info(message)
    script = f"""
        (function() {{
            var el = document.getElementById({json.dumps(_OVERLAY_ELEMENT_ID)});
            if (!el) {{
                el = document.createElement('div');
                el.id = {json.dumps(_OVERLAY_ELEMENT_ID)};
                el.style.position = 'fixed';
                el.style.top = '0';
                el.style.left = '0';
                el.style.width = '100%';
                el.style.height = '100%';
                el.style.background = 'rgba(0, 0, 0, 0.75)';
                el.style.color = '#fff';
                el.style.display = 'flex';
                el.style.alignItems = 'center';
                el.style.justifyContent = 'center';
                el.style.fontSize = '18px';
                el.style.fontFamily = 'sans-serif';
                el.style.zIndex = '2147483647';
                document.body.appendChild(el);
            }}
            el.textContent = {json.dumps(message)};
        }})();
    """
    try:
        window.evaluate_js(script)
    except Exception:
        logger.warning("Could not update in-page status overlay", exc_info=True)


def _clear_status(window):
    script = f"""
        (function() {{
            var el = document.getElementById({json.dumps(_OVERLAY_ELEMENT_ID)});
            if (el) {{ el.remove(); }}
        }})();
    """
    try:
        window.evaluate_js(script)
    except Exception:
        logger.warning("Could not clear in-page status overlay", exc_info=True)


def run_manual_check(window):
    """Entry point for the "Check for Updates" menu item. Runs on a
    pywebview-managed background thread (confirmed in pywebview's cocoa
    backend: menu actions are dispatched via `Thread(...).start()`), so this
    avoids tkinter (main-thread only) and instead uses pywebview's own
    thread-safe `window.create_confirmation_dialog` and `window.evaluate_js`."""
    if not _update_lock.acquire(blocking=False):
        logger.info("Manual update check requested while an update is already in progress, skipping")
        window.create_confirmation_dialog("Update in progress", "An update check or install is already running.")
        return
    try:
        _run_manual_check_locked(window)
    finally:
        _update_lock.release()


def _run_manual_check_locked(window):
    logger.info("Manual update check requested (current version %s)", __version__)
    _set_status(window, "Checking for updates...")

    try:
        release = get_latest_release()
    except Exception as exc:
        logger.warning("Manual update check failed: %s", exc)
        _clear_status(window)
        window.create_confirmation_dialog("Update check failed", str(exc))
        return

    remote_version = release["tag_name"].lstrip("v")
    if not is_newer(release):
        logger.info("Manual update check: up to date (latest release is %s)", remote_version)
        _clear_status(window)
        window.create_confirmation_dialog("Up to date", f"You are running the latest version (v{__version__}).")
        return

    logger.info("Manual update check: newer release found: %s", remote_version)

    if not getattr(sys, "frozen", False):
        logger.info("Running from source; not offering to install %s", remote_version)
        _clear_status(window)
        return

    _clear_status(window)
    confirmed = window.create_confirmation_dialog(
        "Update available",
        f"A new version is available: v{remote_version} (you have v{__version__}). Update now?",
    )
    logger.info("Manual update dialog choice: %s", "update" if confirmed else "later")
    if not confirmed:
        return

    _set_status(window, "Downloading update...")
    try:
        asset_url = find_asset_url(release)
        if asset_url is None:
            raise RuntimeError(f"no release asset for platform {sys.platform!r}")
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        download_asset(asset_url, tmp_path)
        logger.info("Downloaded update asset, installing %s", remote_version)
        _set_status(window, "Installing update...")
        write_update_marker(__version__)
        install(tmp_path)  # dispatches to the platform installer, then exits
    except Exception as exc:
        logger.error("Manual update install failed: %s", exc)
        _clear_status(window)
        window.create_confirmation_dialog("Update failed", f"MAVEN could not download or install the update.\n\nDetails: {exc}")
