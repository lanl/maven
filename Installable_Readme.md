# MAVEN Desktop Packaging

This document covers the new desktop-app packaging layer added on top of the
existing `maven` CLI: a native window wrapper, a self-updater, and a GitHub
Actions release pipeline that builds installers for Windows, macOS, and
Linux. The original `pip install . && maven` (browser-based) workflow is
unchanged and still works exactly as before — this is an additive
distribution channel, not a replacement.

## Running it locally

### Option A: existing CLI (dev/browser flow, unchanged)

```
pip install -r requirements.txt
pip install -e .
maven
```

Opens a localhost URL for you to load in your own browser, same as always.

### Option B: desktop window (new)

Requires Python 3.12+ and the packaging-only dependencies in addition to the
app's normal dependencies:

```
pip install -r requirements.txt -r requirements-packaging.txt
pip install -e .
python -m maven.desktop.desktop_main
```

This starts the same Streamlit app in-process on a background thread and
opens it in a native `pywebview` window (with a menu bar: "Check for
Updates" and "Export Logs...") instead of pointing you at a browser.

### Option C: build a standalone executable locally

```
pip install -r requirements.txt -r requirements-packaging.txt
pyinstaller packaging/maven.spec
./dist/maven-desktop        # macOS/Linux
dist\maven-desktop.exe      # Windows
```

To match the name a release build would produce, set
`MAVEN_PYINSTALLER_NAME` first, e.g. `MAVEN_PYINSTALLER_NAME=maven-macos
pyinstaller packaging/maven.spec`.

The first build on a machine takes several minutes (PyInstaller has to
analyze and bundle Streamlit, LangChain, ursa-ai, and dsi-workflow) and
produces a single-file executable around 250 MB.

## How a release ships (CI)

Pushing an annotated tag matching `v*.*.*` (e.g. `git tag v1.1.0 && git push
origin v1.1.0`) triggers `.github/workflows/release.yml`, which:

1. Stamps `maven/_version.py` with the tag's version.
2. Builds the PyInstaller executable on Windows, macOS, and Linux runners in
   parallel via `packaging/maven.spec`.
3. Wraps each platform's binary into a native installer: an NSIS installer
   (`.exe`) on Windows, a `.dmg` on macOS, an AppImage on Linux.
4. Publishes a GitHub Release on the tag with all six artifacts (three raw
   binaries the self-updater downloads, three installers end users
   download for a first install).

No GitHub secrets are required — `lanl/maven` is a public repo, so the
self-updater calls the Releases API anonymously.

## What's new / changed

### New: `maven/desktop/` subpackage

A self-contained wrapper around the existing Streamlit app, kept separate
from `maven/app.py` and `maven/cli.py` so the plain `pip install` flow never
needs any of these extra dependencies.

| File | Purpose |
|---|---|
| `paths.py` | Resolves data file paths correctly both for a normal install and inside a frozen PyInstaller binary (`sys._MEIPASS`); also provides a shared per-user data directory (`~/.maven_config/desktop_data`). |
| `streamlit_runner.py` | Starts the Streamlit server in-process on a background thread via `streamlit.web.bootstrap.run()`, instead of `cli.py`'s subprocess-based `streamlit run` (which doesn't work inside a frozen one-file binary — there's no `python` to re-invoke). Disables Streamlit's OS signal-handler installation, since that requires the main thread and pywebview needs the main thread on macOS. |
| `gui.py` | Opens the Streamlit UI in a native `pywebview` window with a menu bar ("Check for Updates", "Export Logs..."). |
| `desktop_main.py` | Entry point: runs the update check, then starts the Streamlit thread and opens the window. This is what gets built into the packaged executable. |
| `updater.py` | Self-updater: checks `lanl/maven`'s GitHub Releases for a newer version, prompts the user (becomes mandatory 7 days after a release ships), downloads the right installer for the platform, and swaps itself in place. Uses the OS trust store (via `truststore`) for HTTPS instead of the bundled `certifi` CA list, so it keeps working behind TLS-inspecting proxies — never fixed by bundling a certificate into the repo. |
| `wrapper_log.py` | Shared JSON-lines logger at `<data_dir>/wrapper.log`, since a windowed packaged app has no visible console output. |

### New: `packaging/`

| File | Purpose |
|---|---|
| `maven.spec` | PyInstaller build spec. Explicitly bundles Streamlit's static assets and the dynamic/plugin-style imports used by `ursa-ai`, `langchain`, and `dsi-workflow` (via `collect_all`), plus `maven/app.py`'s data files (`metadata_template/`, `remote_move.py`, `remote_register_endpoint.py`, `.streamlit/`) that aren't otherwise picked up because they're read as text/data, not imported as code. |
| `icon.png` | Placeholder 512x512 app icon — swap with real branding later. |
| `windows/installer.nsi` | NSIS installer script; per-user install under `%LOCALAPPDATA%\Programs\maven`, no admin/UAC required (so the self-updater can overwrite the exe in place). |
| `macos/Info.plist.template` | `.app` bundle metadata template (bundle ID `org.lanl.maven`); version placeholder filled in by CI. |
| `linux/maven.desktop.template` | Linux desktop entry template bundled into the AppImage. |

### New: `.github/workflows/release.yml`

GitHub Actions release pipeline, described above.

### New: `requirements-packaging.txt`

Packaging-only dependencies, deliberately kept **separate** from
`requirements.txt` so a plain `pip install maven-data` (including headless
HPC users) never pulls in desktop GUI toolkit bindings:

- `pyinstaller` — builds the standalone executable
- `pywebview` — native window wrapper (pulls in platform-specific GUI
  bindings: PyObjC on macOS, pythonnet/WebView2 on Windows, PyGObject/
  WebKitGTK on Linux)
- `truststore` — OS-trust-store HTTPS verification for the updater
- `packaging` — semantic version parsing/comparison for the updater

### Modified: `maven/app.py`

The three places that read bundled files relative to `Path(__file__).parent`
(the `metadata_template/` YAML/MD files, and the raw-text reads of
`remote_move.py`/`remote_register_endpoint.py`) now go through
`maven.desktop.paths.resource_path()` instead, so they resolve correctly
whether running from a normal install or from inside a frozen PyInstaller
binary. No other logic changed.

### Modified: `requirements.txt`

Added `requests` — `app.py` already imports it directly, but it was missing
from the declared dependencies (previously working only because something
else transitively installed it).

### Modified: `.gitignore`

Added `!packaging/maven.spec` — the repo's blanket `*.spec` ignore rule
would otherwise exclude this intentionally-committed build spec.

## Installing the macOS `.dmg`

Since the `.dmg` is only ad-hoc codesigned (no Apple Developer ID / no
notarization), Gatekeeper treats it as "unidentified developer" at best, and
on some machines refuses to open it at all with a "is damaged and can't be
opened" message. To install:

1. Open the `.dmg` and drag `maven.app` into `/Applications`.
2. Try launching it normally first: right-click (or Control-click)
   `maven.app` → **Open**, then confirm the "unidentified developer" prompt.
   This works on most machines and only needs to be done once.
3. If step 2 doesn't offer an "Open" option, or macOS claims the app is
   damaged, Gatekeeper is refusing to honor the ad-hoc signature at all.
   Clear the quarantine extended attribute macOS attaches to anything
   downloaded from the internet, which re-signs it as adhoc-trusted locally:

   ```
   xattr -cr /Applications/maven.app
   ```

   This strips the `com.apple.quarantine` flag (and any other extended
   attributes) recursively from the app bundle, so Gatekeeper no longer
   evaluates it against the (missing) notarization/Developer ID checks.
   This is a one-time, per-machine workaround — it doesn't persist across
   reinstalling or updating the app, so re-run it if a future self-update
   re-triggers the same warning.

## Known limitations / things to validate further

- **Binary size**: ~250 MB per platform (Streamlit + pandas + LangChain +
  ursa-ai + dsi-workflow bundled into one file). Acceptable for now; revisit
  `--onefile` vs `--onedir` if download size becomes a problem.
- **macOS Gatekeeper**: the `.dmg` is ad-hoc codesigned (no Apple Developer
  ID), so first launch requires right-click → Open to bypass the
  "unidentified developer" warning.
- **Windows WebView2**: `pywebview`'s Windows backend needs the Edge WebView2
  runtime, which ships with modern Windows but isn't guaranteed present on
  older/locked-down images. Not yet validated against LANL's managed Windows
  baseline.
