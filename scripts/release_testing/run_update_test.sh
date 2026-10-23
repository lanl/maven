#!/bin/bash
# Orchestrates a full local test of maven's self-update flow against the
# real /Applications/MAVEN.app, without creating any GitHub release:
#
#   1. Builds a bumped-version .dmg locally (build_dmg.sh), the same way
#      .github/workflows/release.yml's macOS job would.
#   2. Generates (if needed) a throwaway local CA + api.github.com leaf cert
#      (gen_local_ca.sh) and temporarily trusts the CA in the System
#      keychain.
#   3. Temporarily redirects api.github.com to 127.0.0.1 via /etc/hosts.
#   4. Runs fake_github_server.py on 127.0.0.1:443, advertising the bumped
#      version with the dmg built in step 1 as its release asset.
#   5. Opens /Applications/MAVEN.app so its real, unmodified startup update
#      check (maven/desktop/updater.py) finds that "release" and runs the
#      real download/install/relaunch flow end to end.
#
# All system-wide state changes (System keychain trust, /etc/hosts) are
# undone on exit via a trap, even on failure/Ctrl-C. Use --cleanup-only to
# force that teardown if a previous run was interrupted before its trap ran.
#
# This script does NOT touch the maven source tree's version file after it
# finishes, and never deletes/recreates /Applications/MAVEN.app itself --
# the file swap there is performed entirely by the existing, unmodified
# updater.py code, run for real.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script_dir="$repo_root/scripts/release_testing"
out_dir="$script_dir/out"
ca_dir="$script_dir/.ca"
ca_cert="$ca_dir/ca.pem"
ca_name="maven-local-update-test-CA"
hosts_marker="# maven-local-update-test"
hosts_line="127.0.0.1 api.github.com $hosts_marker"
pid_file="$out_dir/fake_github_server.pid"
server_log="$out_dir/fake_github_server.log"
installed_app="/Applications/MAVEN.app"

cleanup() {
    echo "==> Cleaning up"

    if [ -f "$pid_file" ]; then
        server_pid="$(cat "$pid_file" 2>/dev/null || true)"
        if [ -n "${server_pid:-}" ] && kill -0 "$server_pid" 2>/dev/null; then
            echo "    stopping fake_github_server.py (pid $server_pid)"
            sudo kill "$server_pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
    fi

    if grep -qF "$hosts_marker" /etc/hosts 2>/dev/null; then
        echo "    removing /etc/hosts redirect"
        sudo sed -i '' "/$hosts_marker/d" /etc/hosts
    fi

    if security find-certificate -c "$ca_name" /Library/Keychains/System.keychain >/dev/null 2>&1; then
        echo "    removing local CA trust + keychain entry"
        if [ -f "$ca_cert" ]; then
            sudo security remove-trusted-cert -d "$ca_cert" 2>/dev/null || true
        fi
        sudo security delete-certificate -c "$ca_name" /Library/Keychains/System.keychain 2>/dev/null || true
    fi
}

if [ "${1:-}" = "--cleanup-only" ]; then
    cleanup
    echo "==> Cleanup-only run complete"
    exit 0
fi

trap cleanup EXIT INT TERM

echo "==> This will temporarily trust a local CA system-wide, redirect"
echo "    api.github.com in /etc/hosts, and run the real self-update install"
echo "    against $installed_app. You'll be asked for your password"
echo "    (sudo) and macOS's own admin prompt (the app's own install step)."
read -r -p "    Continue? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Aborted."
    trap - EXIT INT TERM
    exit 1
fi

if [ ! -d "$installed_app" ]; then
    echo "error: $installed_app not found -- install MAVEN.app there first" >&2
    exit 1
fi

current_version="$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$installed_app/Contents/Info.plist")"
echo "==> Installed app reports version $current_version"

test_version="$(python3 -c "
import sys
parts = '$current_version'.split('.')
parts = [int(p) for p in parts] if all(p.isdigit() for p in parts) else [0, 0, 0]
while len(parts) < 3:
    parts.append(0)
parts[-1] += 1
print('.'.join(str(p) for p in parts))
")"
echo "==> Test release will advertise version $test_version"

mkdir -p "$out_dir"

echo "==> Building test .dmg"
"$script_dir/build_dmg.sh" "$test_version" "$out_dir"
dmg_path="$out_dir/maven-macos-installer.dmg"

echo "==> Preparing local CA"
"$script_dir/gen_local_ca.sh" "$ca_dir"

echo "==> Trusting local CA in the System keychain (sudo required)"
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$ca_cert"

echo "==> Redirecting api.github.com to 127.0.0.1 in /etc/hosts (sudo required)"
if grep -qF "$hosts_marker" /etc/hosts 2>/dev/null; then
    sudo sed -i '' "/$hosts_marker/d" /etc/hosts
fi
printf '%s\n' "$hosts_line" | sudo tee -a /etc/hosts >/dev/null

echo "==> Starting fake GitHub server on 127.0.0.1:443 (sudo required for port 443)"
rm -f "$pid_file" "$server_log"
sudo python3 "$script_dir/fake_github_server.py" \
    --dmg-path "$dmg_path" \
    --version "$test_version" \
    --cert "$ca_dir/leaf.pem" \
    --key "$ca_dir/leaf.key" \
    --port 443 \
    --pid-file "$pid_file" \
    > "$server_log" 2>&1 &

for _ in $(seq 1 20); do
    [ -f "$pid_file" ] && break
    sleep 0.25
done
if [ ! -f "$pid_file" ]; then
    echo "error: fake_github_server.py did not start; see $server_log" >&2
    exit 1
fi
echo "    server log: $server_log"

echo "==> Launching $installed_app"
open -n "$installed_app"

cat <<EOF

==> MAVEN is starting. Its own startup update check should find version
    $test_version and prompt to update. Walk through the dialog/admin
    prompt/relaunch as a real user would.

    Logs to watch while this runs:
      ~/.maven_config/desktop_data/wrapper.log
      ~/.maven_config/desktop_data/install_trace.log
      ~/.maven_config/desktop_data/relaunch_stdio.log

EOF
read -r -p "Press Enter once you're done observing the update (this tears down the local CA/hosts/server): " _
