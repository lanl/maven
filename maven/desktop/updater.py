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
import os
import shutil
import subprocess
import sys
import tempfile
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

logger = get_logger("updater")


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


def show_update_complete_dialog(from_version, to_version):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Update complete",
        f"MAVEN was updated from v{from_version} to v{to_version}.",
    )
    root.destroy()


def show_updating_dialog(message="Application updating..."):
    """Non-blocking "please wait" window shown while a download/install is
    in progress. The process calls os._exit() once the platform installer
    script is handed off, so this window is torn down with the process --
    nothing needs to explicitly close it."""
    root = tk.Tk()
    root.title("MAVEN")
    root.resizable(False, False)
    tk.Label(root, text=message, padx=30, pady=20).pack()
    root.eval("tk::PlaceWindow . center")
    root.update()
    return root


def prompt_update_dialog(current_version, remote_version, deadline, mandatory):
    """Shows a blocking Tk dialog and returns "update", "later", or "quit"."""
    result = {"choice": "quit" if mandatory else "later"}

    root = tk.Tk()
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

    root.eval("tk::PlaceWindow . center")
    root.mainloop()

    return result["choice"]


def _write_and_launch(script_path, script_body, launch_cmd):
    with open(script_path, "w") as f:
        f.write(script_body)
    os.chmod(script_path, 0o755)
    subprocess.Popen(launch_cmd, close_fds=True, start_new_session=True)


def _install_macos(installer_path, current_exe):
    # current_exe is .../MAVEN.app/Contents/MacOS/maven-macos
    app_bundle = os.path.dirname(os.path.dirname(os.path.dirname(current_exe)))
    apps_dir = os.path.dirname(app_bundle)
    bundle_name = os.path.basename(app_bundle)
    mount_point = tempfile.mkdtemp(prefix="maven-update-")
    pid = os.getpid()

    script_path = os.path.join(tempfile.gettempdir(), "maven_update.sh")
    script_body = f"""#!/bin/sh
while kill -0 {pid} 2>/dev/null; do sleep 0.5; done
hdiutil attach {_sh_quote(installer_path)} -mountpoint {_sh_quote(mount_point)} -nobrowse -quiet
rm -rf {_sh_quote(app_bundle)}
cp -R {_sh_quote(mount_point)}/{_sh_quote(bundle_name)} {_sh_quote(apps_dir)}/
hdiutil detach {_sh_quote(mount_point)} -quiet
rm -f {_sh_quote(installer_path)}
open {_sh_quote(app_bundle)}
rm -f "$0"
"""
    _write_and_launch(script_path, script_body, ["/bin/sh", script_path])
    os._exit(0)


def _install_windows(installer_path, current_exe):
    pid = os.getpid()

    script_path = os.path.join(tempfile.gettempdir(), "maven_update.bat")
    script_body = (
        "@echo off\r\n"
        f":wait\r\n"
        f'tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL\r\n'
        f"if not errorlevel 1 (\r\n"
        f"  ping 127.0.0.1 -n 2 > nul\r\n"
        f"  goto wait\r\n"
        f")\r\n"
        f'"{installer_path}" /S\r\n'
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
    target = os.environ.get("APPIMAGE") or current_exe
    pid = os.getpid()

    script_path = os.path.join(tempfile.gettempdir(), "maven_update.sh")
    script_body = f"""#!/bin/sh
while kill -0 {pid} 2>/dev/null; do sleep 0.5; done
chmod +x {_sh_quote(installer_path)}
mv {_sh_quote(installer_path)} {_sh_quote(target)}
{_sh_quote(target)} &
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
    logger.info("Startup update check: current version is %s", __version__)

    from_version = consume_update_marker()
    if from_version is not None:
        logger.info("Update completed: %s -> %s", from_version, __version__)
        if splash:
            splash.hide()
        show_update_complete_dialog(from_version, __version__)
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
    choice = prompt_update_dialog(__version__, remote_version, deadline, mandatory)
    logger.info("Startup update dialog choice: %s", choice)

    if choice == "later":
        if splash:
            splash.show()
        return
    if choice == "quit":
        sys.exit(0)

    updating_window = show_updating_dialog()
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


def _set_status(window, message):
    logger.info(message)


def run_manual_check(window):
    """Entry point for the "Check for Updates" menu item. Runs on a
    pywebview-managed background thread (confirmed in pywebview's cocoa
    backend: menu actions are dispatched via `Thread(...).start()`), so this
    avoids tkinter (main-thread only) and instead uses pywebview's own
    thread-safe `window.create_confirmation_dialog`."""
    logger.info("Manual update check requested (current version %s)", __version__)
    _set_status(window, "Checking for updates...")

    try:
        release = get_latest_release()
    except Exception as exc:
        logger.warning("Manual update check failed: %s", exc)
        window.create_confirmation_dialog("Update check failed", str(exc))
        return

    remote_version = release["tag_name"].lstrip("v")
    if not is_newer(release):
        logger.info("Manual update check: up to date (latest release is %s)", remote_version)
        window.create_confirmation_dialog("Up to date", f"You are running the latest version (v{__version__}).")
        return

    logger.info("Manual update check: newer release found: %s", remote_version)

    if not getattr(sys, "frozen", False):
        logger.info("Running from source; not offering to install %s", remote_version)
        return

    confirmed = window.create_confirmation_dialog(
        "Update available",
        f"A new version is available: v{remote_version} (you have v{__version__}). Update now?",
    )
    logger.info("Manual update dialog choice: %s", "update" if confirmed else "later")
    if not confirmed:
        return

    _set_status(window, "Application updating...")
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
        logger.error("Manual update install failed: %s", exc)
