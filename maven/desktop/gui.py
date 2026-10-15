"""Native window embedding the Streamlit UI, so the packaged app shows up
as a real desktop app (Dock/taskbar entry, native menu) instead of running
headless and sending the user out to their own browser like the `maven`
CLI's `streamlit run` + localhost-URL flow does today."""
import sys
import time
import urllib.request

import webview
from webview.menu import Menu, MenuAction

from maven.desktop.updater import run_manual_check
from maven.desktop.wrapper_log import export_logs, get_logger

logger = get_logger("gui")


def _set_macos_app_name():
    """Dev-mode `python -m` runs have no app bundle, so macOS falls back to
    showing "Python" in the Dock/menu bar. Patch the in-memory bundle info
    pywebview's Cocoa backend reads so it shows "MAVEN" instead, matching
    the packaged app's Info.plist."""
    if sys.platform != "darwin":
        return
    try:
        from AppKit import NSBundle

        NSBundle.mainBundle().infoDictionary()["CFBundleName"] = "MAVEN"
    except Exception:
        logger.warning("Could not set macOS app name", exc_info=True)


def _wait_for_server(url, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def export_logs_action(window):
    path = window.create_file_dialog(
        webview.SAVE_DIALOG,
        save_filename="maven-wrapper-log.json",
        file_types=("JSON Files (*.json)", "Text Files (*.txt)"),
    )
    if not path:
        return
    dest = path[0] if isinstance(path, (list, tuple)) else path
    export_logs(dest)
    logger.info("Exported logs to %s", dest)


def run_gui(port):
    _set_macos_app_name()
    url = f"http://127.0.0.1:{port}/"
    logger.info("Waiting for Streamlit server to come up")
    if not _wait_for_server(url):
        logger.error("Streamlit server did not come up within timeout")

    logger.info("Opening main window")
    window = webview.create_window("MAVEN", url, width=1280, height=900)
    menu = [
        Menu(
            "Help",
            [
                MenuAction("Check for Updates", lambda: run_manual_check(window)),
                MenuAction("Export Logs...", lambda: export_logs_action(window)),
            ],
        )
    ]
    webview.start(menu=menu)
