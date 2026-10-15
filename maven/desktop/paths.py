"""Path resolution for data files bundled with the desktop (PyInstaller)
build, usable both from a normal pip install and from a frozen --onefile
binary (where loose files only exist extracted under sys._MEIPASS)."""
import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS) / "maven"
    else:
        base = Path(__file__).resolve().parent.parent  # maven/maven/
    return base.joinpath(*parts)


def get_icon_path() -> Path:
    """App icon, used for both the window/taskbar icon and the startup
    splash screen. Lives under packaging/ (not maven/) in the source tree
    since it's also consumed by the per-platform build scripts, so it needs
    its own lookup instead of resource_path()'s maven-package convention."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "maven" / "icon.png"
    return Path(__file__).resolve().parent.parent.parent / "packaging" / "icon.png"


def get_data_dir() -> Path:
    data_dir = Path.home() / ".maven_config" / "desktop_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
