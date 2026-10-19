from maven._version import __version__
from maven.desktop import gui
from maven.desktop.splash import Splash
from maven.desktop.streamlit_runner import start_streamlit_background
from maven.desktop.updater import check_and_apply_update
from maven.desktop.wrapper_log import get_logger

logger = get_logger("main")


def run(splash):
    print(f"MAVEN {__version__}")
    _thread, port = start_streamlit_background()
    gui.run_gui(port, splash)


def main():
    logger.info("Starting MAVEN desktop %s", __version__)
    gui._set_macos_app_name()
    splash = Splash()
    try:
        check_and_apply_update(splash)
        run(splash)
    except Exception:
        logger.error("Unhandled error, exiting", exc_info=True)
        raise
    finally:
        splash.destroy()


if __name__ == "__main__":
    main()
