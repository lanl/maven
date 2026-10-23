# Local self-update test harness (macOS)

Tests the real self-update flow (`maven/desktop/updater.py`) end to end --
check, download, install, relaunch -- against a locally built `.dmg`,
without pushing a git tag or publishing a GitHub release. No code in
`maven/` is modified or special-cased for this; the fake release is served
over a real TLS connection to the hostname the app already talks to.

## How it works

1. `build_dmg.sh` builds a `.app` + `.dmg` the same way the macOS job in
   `.github/workflows/release.yml` does, bumped one patch version above
   whatever's currently in `/Applications/MAVEN.app`.
2. `gen_local_ca.sh` generates a throwaway local CA and a leaf certificate
   for `api.github.com`, signed by that CA.
3. `run_update_test.sh` ties it together:
   - Temporarily trusts the local CA in the macOS System keychain.
   - Temporarily redirects `api.github.com` to `127.0.0.1` in `/etc/hosts`.
   - Runs `fake_github_server.py`, which answers the two GitHub Releases
     API calls `updater.py` makes (list releases, download asset) with the
     bumped version and the `.dmg` from step 1.
   - Opens `/Applications/MAVEN.app` so its own startup update check finds
     that "release" and runs the real install/relaunch code path.
   - On exit (including Ctrl-C or a failure), removes the CA trust and the
     `/etc/hosts` line again.

## Usage

```sh
scripts/release_testing/run_update_test.sh
```

Follow the prompts; it asks for `sudo` (needed for keychain trust, the
`/etc/hosts` edit, and binding port 443) and will pause so you can watch
the real update dialog, the AppleScript admin prompt, and the relaunch.
While it's running, these logs are useful:

```
~/.maven_config/desktop_data/wrapper.log
~/.maven_config/desktop_data/install_trace.log
~/.maven_config/desktop_data/relaunch_stdio.log
```

If a run is interrupted before cleanup finishes, recover with:

```sh
scripts/release_testing/run_update_test.sh --cleanup-only
```

## Prerequisites

- `brew install create-dmg`
- The project's `.venv` with `pyinstaller` installed (`pip install -r
  requirements.txt -r requirements-packaging.txt`)
- `/Applications/MAVEN.app` already installed (any version) -- that's the
  app under test.

## Important: this touches system-wide state and your real install

- It adds (and removes) a trusted root certificate in the **System**
  keychain, and a line in `/etc/hosts` -- both `sudo`-gated and scoped to
  one run, but still machine-wide while active.
- It overwrites `/Applications/MAVEN.app` for real, via the update flow's
  own install code -- the exact same thing a real update would do. Don't
  run this if you need to keep your currently-installed version.
- The generated CA and the built `.dmg`/`.app` live under this directory
  (`.ca/`, `out/`) and are gitignored -- never commit them.
