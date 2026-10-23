#!/bin/bash
# Builds a macOS .app + .dmg exactly the way .github/workflows/release.yml's
# macOS job does, but locally -- so the artifact under test matches what CI
# would produce without actually pushing a tag / publishing a release.
#
# Usage: build_dmg.sh <version> <output_dir>
#   version: e.g. 1.0.6 (no leading "v"), stamped into maven/_version.py and
#            the app bundle's Info.plist for the duration of this build.
#   output_dir: where release/MAVEN.app and release/maven-macos-installer.dmg
#               end up (as out_dir/MAVEN.app, out_dir/maven-macos-installer.dmg).
set -euo pipefail

if [ $# -ne 2 ]; then
    echo "usage: $0 <version> <output_dir>" >&2
    exit 1
fi

version="$1"
out_dir="$2"
asset_name="maven-macos"
pyinstaller_name="maven-macos"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

venv_bin="$repo_root/.venv/bin"
if [ -x "$venv_bin/pyinstaller" ]; then
    PATH="$venv_bin:$PATH"
fi

version_file="maven/_version.py"
version_backup="$(mktemp)"
cp "$version_file" "$version_backup"
restore_version() {
    cp "$version_backup" "$version_file"
    rm -f "$version_backup"
}
trap restore_version EXIT

echo "==> Stamping version $version into $version_file"
printf '__version__ = "%s"\n' "$version" > "$version_file"

echo "==> Building with PyInstaller"
MAVEN_PYINSTALLER_NAME="$pyinstaller_name" pyinstaller packaging/maven.spec

mkdir -p "$out_dir"
rm -rf "$out_dir/MAVEN.app" "$out_dir/maven-macos-installer.dmg"

echo "==> Assembling MAVEN.app bundle"
app_dir="$out_dir/MAVEN.app"
mkdir -p "$app_dir/Contents/MacOS" "$app_dir/Contents/Resources"
cp "dist/$pyinstaller_name" "$app_dir/Contents/MacOS/$asset_name"
chmod +x "$app_dir/Contents/MacOS/$asset_name"
sed "s/__VERSION__/$version/g" packaging/macos/Info.plist.template > "$app_dir/Contents/Info.plist"

icon_tmp="$(mktemp -d)"
iconset="$icon_tmp/icon.iconset"
mkdir -p "$iconset"
sips -z 512 512 packaging/icon.png --out "$iconset/icon_512x512.png" >/dev/null
sips -z 256 256 packaging/icon.png --out "$iconset/icon_256x256.png" >/dev/null
sips -z 128 128 packaging/icon.png --out "$iconset/icon_128x128.png" >/dev/null
sips -z 32 32 packaging/icon.png --out "$iconset/icon_32x32.png" >/dev/null
sips -z 16 16 packaging/icon.png --out "$iconset/icon_16x16.png" >/dev/null
iconutil -c icns "$iconset" -o "$app_dir/Contents/Resources/icon.icns"
rm -rf "$icon_tmp"

echo "==> Ad-hoc codesigning"
codesign --force --deep -s - "$app_dir"

if ! command -v create-dmg >/dev/null 2>&1; then
    echo "create-dmg not found; install with: brew install create-dmg" >&2
    exit 1
fi

echo "==> Building .dmg"
dmg_staging="$(mktemp -d)"
mv "$app_dir" "$dmg_staging/MAVEN.app"

dmg_path="$out_dir/maven-macos-installer.dmg"

create-dmg \
    --volname "MAVEN" \
    --window-size 660 400 \
    --icon-size 128 \
    --icon "MAVEN.app" 160 185 \
    --hide-extension "MAVEN.app" \
    --app-drop-link 480 185 \
    --no-internet-enable \
    "$dmg_path" \
    "$dmg_staging" || true

test -f "$dmg_path"

mv "$dmg_staging/MAVEN.app" "$app_dir"
rm -rf "$dmg_staging"

echo "==> Built $dmg_path (version $version)"
echo "==> Bundle also available unpacked at $app_dir"
