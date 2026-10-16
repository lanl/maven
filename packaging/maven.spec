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
#
# app.py itself is also never imported by name -- streamlit_runner.py hands
# its path to Streamlit's bootstrap API at runtime instead -- so PyInstaller's
# static analysis never walks app.py's own `from maven.x import y` statements
# and silently drops maven's submodules (ursa_autofill, tier1_genesis_dc_agent,
# migrations, ursa_utils) from the frozen build. collect_submodules("maven")
# forces all of them in as hidden imports.
#
# collect_submodules() imports the "maven" package itself to walk it, so repo_root
# must be on sys.path *before* that call. The release workflow never installs the
# maven package (only its runtime dependencies), so without this, collect_submodules
# silently returns [] and the build ships without those submodules even though it
# works for anyone with an editable/local install of maven on their machine.
import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None
repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(SPEC)), ".."))
sys.path.insert(0, repo_root)

datas = []
binaries = []
hiddenimports = collect_submodules("maven")

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
