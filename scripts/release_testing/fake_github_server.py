#!/usr/bin/env python3
"""Stdlib-only HTTPS server that stands in for api.github.com, serving just
enough of the GitHub Releases API for maven/desktop/updater.py's unmodified
get_latest_release() / download_asset() to treat a locally-built .dmg as a
real newer release.

Must be reached via a real TLS handshake against the hostname
"api.github.com" (via a temporary /etc/hosts redirect to 127.0.0.1) using a
cert chain the OS trust store accepts (via gen_local_ca.sh's CA, temporarily
trusted in the System keychain) -- see run_update_test.sh, which wires both
of those up before starting this server.

Endpoints:
  GET /repos/lanl/maven/releases
      -> JSON array with one synthetic release.
  GET /repos/lanl/maven/releases/assets/1
      -> the .dmg file's raw bytes.
"""
import argparse
import http.server
import json
import os
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = "lanl/maven"
ASSET_NAME = "maven-macos-installer.dmg"


def make_handler(dmg_path: Path, version: str, published_at: str):
    releases_path = f"/repos/{REPO}/releases"
    asset_path = f"/repos/{REPO}/releases/assets/1"
    asset_url = f"https://api.github.com{asset_path}"

    class Handler(http.server.BaseHTTPRequestHandler):
        def _send_json(self, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == releases_path:
                self._send_json(
                    [
                        {
                            "tag_name": f"v{version}",
                            "draft": False,
                            "prerelease": False,
                            "published_at": published_at,
                            "assets": [
                                {"name": ASSET_NAME, "url": asset_url},
                            ],
                        }
                    ]
                )
            elif self.path == asset_path:
                data = dmg_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, fmt, *args):
            sys.stderr.write(f"[fake_github_server] {fmt % args}\n")

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dmg-path", required=True, type=Path)
    parser.add_argument("--version", required=True, help='e.g. "1.0.6" (no leading v)')
    parser.add_argument("--cert", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument(
        "--published-at",
        default=None,
        help="ISO8601 UTC timestamp; defaults to now (keeps the update non-mandatory)",
    )
    parser.add_argument(
        "--pid-file",
        type=Path,
        default=None,
        help="Written with this process's own pid as soon as the server is listening -- "
        "needed because this process is typically started via `sudo` (port 443 requires "
        "root), so the caller's $! only reflects sudo's pid, not necessarily this one.",
    )
    args = parser.parse_args()

    if not args.dmg_path.is_file():
        parser.error(f"dmg not found: {args.dmg_path}")

    if args.pid_file is not None:
        args.pid_file.write_text(str(os.getpid()))

    published_at = args.published_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    handler = make_handler(args.dmg_path, args.version, published_at)
    server = http.server.HTTPServer(("127.0.0.1", args.port), handler)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(args.cert), keyfile=str(args.key))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)

    print(
        f"[fake_github_server] serving version {args.version} "
        f"(dmg={args.dmg_path}) on https://127.0.0.1:{args.port}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
