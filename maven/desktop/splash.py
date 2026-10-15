"""Startup splash window shown while the update check and Streamlit server
boot run, so the user isn't staring at nothing for the 10-30s between
double-clicking the app and the main pywebview window appearing.

A plain tkinter.Tk (not Toplevel) is used because this needs to exist and
be visible before any other Tk root does -- update.py's dialogs each create
their own throwaway Tk() root, so this one must be hidden/shown around them
rather than coexisting as a second top-level window (tkinter only supports
one Tk() instance safely).
"""
import tkinter as tk

from maven.desktop.paths import get_icon_path
from maven.desktop.wrapper_log import get_logger

logger = get_logger("splash")


class Splash:
    def __init__(self):
        self._root = None
        try:
            self._root = tk.Tk()
            self._root.title("MAVEN")
            self._root.overrideredirect(True)
            self._root.resizable(False, False)

            icon_path = get_icon_path()
            if icon_path.exists():
                image = tk.PhotoImage(file=str(icon_path))
                # Large source icon (512x512); subsample to a reasonable
                # splash size without bundling a second image asset.
                image = image.subsample(4, 4)
                self._icon_image = image  # keep a reference, Tk drops GC'd images
                tk.Label(self._root, image=image).pack(padx=20, pady=(20, 10))

            tk.Label(self._root, text="MAVEN is starting...").pack(padx=20, pady=(0, 20))
            self._root.eval("tk::PlaceWindow . center")
            self._root.update()
        except Exception:
            logger.warning("Could not create splash window", exc_info=True)
            self._root = None

    def pump(self):
        if self._root is None:
            return
        try:
            self._root.update()
        except Exception:
            logger.warning("Splash window closed unexpectedly", exc_info=True)
            self._root = None

    def hide(self):
        if self._root is None:
            return
        try:
            self._root.withdraw()
        except Exception:
            logger.warning("Could not hide splash window", exc_info=True)

    def show(self):
        if self._root is None:
            return
        try:
            self._root.deiconify()
            self._root.update()
        except Exception:
            logger.warning("Could not show splash window", exc_info=True)

    def destroy(self):
        if self._root is None:
            return
        try:
            self._root.destroy()
        except Exception:
            logger.warning("Could not destroy splash window", exc_info=True)
        finally:
            self._root = None
