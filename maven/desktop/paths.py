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


def get_data_dir() -> Path:
    data_dir = Path.home() / ".maven_config" / "desktop_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
