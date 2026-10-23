# Testing a Self-Update Install Locally (macOS)

This covers how to exercise MAVEN's real self-update flow end to end on your
own machine — check, download, install, relaunch — without pushing a git tag
or publishing a GitHub release. It drives the harness in
`scripts/release_testing/`, which builds a locally-signed `.dmg` one patch
version above whatever's installed, serves it as a fake GitHub release over
a real TLS connection, and lets the unmodified `maven/desktop/updater.py`
code install it against your real `/Applications/MAVEN.app`.

See `scripts/release_testing/README.md` for how the harness is implemented;
this doc is the step-by-step for running it.

## Prerequisites

- `brew install create-dmg`
- The project's `.venv` with the packaging extras installed:
  ```sh
  pip install -r requirements.txt -r requirements-packaging.txt
  ```
- `/Applications/MAVEN.app` already installed (any version) — that's the app
  under test. The harness overwrites it for real.

## Before you run it

- It temporarily trusts a throwaway local CA in the **System** keychain and
  adds a line to `/etc/hosts` redirecting `api.github.com` to `127.0.0.1` —
  both sudo-gated, both undone automatically on exit (even on Ctrl-C).
- It overwrites `/Applications/MAVEN.app` for real, via the update flow's own
  install code — the same thing a real update would do. Don't run this if
  you need to keep your currently-installed version.
- Binding port 443 for the fake release server also requires elevated
  privileges.

## Running it

On most dev machines your own login account is already in the admin group,
so you can just run:

```sh
scripts/release_testing/run_update_test.sh
```

and leave the "admin username for sudo" prompt blank — it'll `sudo` as your
current user.

On a machine where elevation requires a **separate** admin account (not just
your own password), set `MAVEN_SUDO_ADMIN` to that account's username so the
script's `sudo` calls run as that account instead of prompting:

```sh
MAVEN_SUDO_ADMIN=L000000 scripts/release_testing/run_update_test.sh
```

(`L000000` above is a placeholder — substitute your actual admin account.)

Either way, walk through the prompts:

1. `Continue? [y/N]` → `y`
2. Password prompt for the admin account (keychain trust, `/etc/hosts` edit,
   binding port 443)
3. The script builds the test `.dmg`, starts the fake release server, and
   runs `open -n /Applications/MAVEN.app`
4. MAVEN's own startup update check should find the fake bumped version and
   show its update dialog — click through it as a real user would
5. Approve the macOS administrator-authorization prompt during install
6. Watch whether the app actually reopens after the relaunch, or repeats a
   bounce/never-reopens symptom
7. Press Enter at the final prompt to tear down the CA trust, `/etc/hosts`
   line, and fake server

## What to check afterward

```sh
~/.maven_config/desktop_data/wrapper.log         # app-level update lifecycle
~/.maven_config/desktop_data/install_trace.log    # step-by-step install script trace
~/.maven_config/desktop_data/relaunch_stdio.log   # captured stdout/stderr of the relaunch attempt
~/.maven_config/desktop_data/failed_update.txt    # present only if the install reported failure
```

If the relaunch fails, `install_trace.log` and `relaunch_stdio.log` are the
most useful — they capture what the install script and the relaunched
process actually did, since both run fully detached from any visible
console.

## Recovering from an interrupted run

If a run is killed before its cleanup trap runs (e.g. the terminal was
closed), the local CA trust, `/etc/hosts` line, or fake server may be left
behind. Force cleanup with the same admin override if needed:

```sh
MAVEN_SUDO_ADMIN=L000000 scripts/release_testing/run_update_test.sh --cleanup-only
```
