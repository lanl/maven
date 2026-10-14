"""Runs the Streamlit app in-process on a background thread, instead of
`cli.py`'s subprocess-based `streamlit run`. A frozen PyInstaller --onefile
binary has no `python` interpreter to re-invoke and app.py isn't a loose
file on disk at runtime, so this uses Streamlit's own bootstrap API
(streamlit.web.bootstrap.run) directly in-process.

Streamlit's bootstrap.run() installs OS signal handlers via signal.signal(),
which only works on the main thread -- but pywebview's macOS (Cocoa) backend
requires NSApplication to run on the main thread too, so one of the two has
to give up the main thread. pywebview wins (it's an OS-level constraint, not
a convenience), so Streamlit's signal handler setup is disabled here: it's
only used for graceful shutdown on SIGTERM/SIGINT, and this app's shutdown
path is "pywebview window closes -> process exits" instead.
"""
from maven.desktop.paths import resource_path

PORT = 8505


def start_streamlit_background():
    import threading

    from streamlit.web import bootstrap

    bootstrap._set_up_signal_handler = lambda server: None

    app_path = str(resource_path("app.py"))
    flag_options = {
        "server.port": PORT,
        "server.headless": True,
        "browser.gatherUsageStats": False,
        "global.developmentMode": False,
    }

    def _run():
        bootstrap.load_config_options(flag_options=flag_options)
        bootstrap.run(app_path, False, [], flag_options)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
