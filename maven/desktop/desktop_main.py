from maven._version import __version__
from maven.desktop import gui
from maven.desktop.streamlit_runner import PORT, start_streamlit_background
from maven.desktop.updater import check_and_apply_update
from maven.desktop.wrapper_log import get_logger

logger = get_logger("main")


def run():
    print(f"MAVEN {__version__}")
    start_streamlit_background()
    gui.run_gui(PORT)


def main():
    logger.info("Starting MAVEN desktop %s", __version__)
    try:
        check_and_apply_update()
        run()
    except Exception:
        logger.error("Unhandled error, exiting", exc_info=True)
        raise


if __name__ == "__main__":
    main()
