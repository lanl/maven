# PyInstaller spec for the maven desktop build.
#
# Built with: pyinstaller packaging/maven.spec
#
# A bare `pyinstaller --onefile main.py` invocation isn't enough here:
# Streamlit ships non-Python static frontend assets, and ursa-ai/langchain/
# dsi-workflow use dynamic/plugin-style imports that PyInstaller's static
# analysis misses by default. collect_all() pulls in each package's full
# data/binary/hidden-import set; app.py's own data files (metadata_template,
# the two remote_*.py scripts it reads as text, .streamlit/config.toml) are
# added explicitly since nothing imports them as code, so PyInstaller's
# import-graph analysis has no way to discover them on its own.
import os

from PyInstaller.utils.hooks import collect_all

block_cipher = None
repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(SPEC)), ".."))

datas = []
binaries = []
hiddenimports = []

for pkg in ("streamlit", "ursa", "langchain", "dsi", "pypdf", "pptx", "docx", "reportlab"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

datas += [
    (os.path.join(repo_root, "maven", "app.py"), "maven"),
    (os.path.join(repo_root, "maven", "metadata_template"), "maven/metadata_template"),
    (os.path.join(repo_root, "maven", "remote_move.py"), "maven"),
    (os.path.join(repo_root, "maven", "remote_register_endpoint.py"), "maven"),
    (os.path.join(repo_root, "maven", ".streamlit"), "maven/.streamlit"),
    (os.path.join(repo_root, "packaging", "icon.png"), "maven"),
]

a = Analysis(
    [os.path.join(repo_root, "maven", "desktop", "desktop_main.py")],
    pathex=[repo_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=os.environ.get("MAVEN_PYINSTALLER_NAME", "maven-desktop"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.environ.get("MAVEN_ICON_PATH"),
)
