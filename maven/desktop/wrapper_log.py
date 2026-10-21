"""Shared JSON-Lines logger for the desktop wrapper (startup, self-update,
menu actions). The Streamlit app's own logic keeps using Streamlit/print
output -- this is only for the wrapper code that has no visible stdout once
packaged as a --windowed PyInstaller build.

Each line in <data_dir>/wrapper.log is one JSON object. Call get_logger(name)
from any desktop module to get a child logger that feeds the one shared file
handler below.

install_crash_logging() makes otherwise-invisible crashes show up here too:
in a --windowed build there's no console for Python's default traceback
printing (sys.excepthook / threading.excepthook) or for faulthandler's
fatal-signal dumps to land on, so both get redirected into this log instead.
A periodic heartbeat is also logged so a crash that doesn't get caught by
either of those (e.g. the whole process being killed) still leaves a last-
known-alive timestamp to bound when it happened.
"""
import atexit
import faulthandler
import json
import logging
import sys
import threading
from datetime import datetime, timezone

from maven.desktop.paths import get_data_dir

LOG_FILENAME = "wrapper.log"
CRASH_LOG_FILENAME = "faulthandler.log"
# Must match updater.INSTALL_TRACE_LOG_FILENAME. Kept as a separate constant
# (rather than importing updater here) since wrapper_log is imported by
# updater.py itself; a back-import would be circular.
INSTALL_TRACE_LOG_FILENAME = "install_trace.log"
HEARTBEAT_INTERVAL_SECONDS = 5 * 60

_root_logger = logging.getLogger("maven.wrapper")
_root_logger.setLevel(logging.INFO)


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(entry)


_log_path = get_data_dir() / LOG_FILENAME
_handler = logging.FileHandler(_log_path)
_handler.setFormatter(_JsonFormatter())
_root_logger.addHandler(_handler)


def get_logger(name):
    return _root_logger.getChild(name)


def read_records():
    if not _log_path.exists():
        return []
    records = []
    with open(_log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _read_crash_dumps():
    """Native (faulthandler) crash dumps live in their own plain-text file,
    not the JSON-Lines wrapper log -- faulthandler writes straight to a file
    object from a signal handler, so it can't go through the logging module's
    formatting machinery. Read back as one string per invocation; most runs
    will have zero."""
    crash_log_path = get_data_dir() / CRASH_LOG_FILENAME
    if not crash_log_path.exists():
        return ""
    return crash_log_path.read_text(encoding="utf-8", errors="replace")


def _read_install_trace_log():
    """The self-update install scripts run after this process has already
    called os._exit(0), so they can't go through the logging module either
    -- they append plain text lines directly to their own file instead (see
    updater._install_trace_log_path()). Most runs will have none."""
    trace_log_path = get_data_dir() / INSTALL_TRACE_LOG_FILENAME
    if not trace_log_path.exists():
        return ""
    return trace_log_path.read_text(encoding="utf-8", errors="replace")


def export_logs(dest_path):
    records = read_records()
    crash_dumps = _read_crash_dumps()
    install_trace = _read_install_trace_log()
    dest_path = str(dest_path)
    if dest_path.lower().endswith(".json"):
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "records": records,
                    "native_crash_dumps": crash_dumps,
                    "install_trace_log": install_trace,
                },
                f,
                indent=2,
            )
    else:
        with open(dest_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(
                    f"{record.get('timestamp', '')} {record.get('level', '')} "
                    f"{record.get('message', '')}\n"
                )
            if crash_dumps:
                f.write("\n--- native crash dumps ---\n")
                f.write(crash_dumps)
            if install_trace:
                f.write("\n--- self-update install trace log ---\n")
                f.write(install_trace)


_crash_logger = get_logger("crash")


def _log_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    _crash_logger.error(
        "Unhandled exception on main thread, process likely about to exit",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def _log_uncaught_thread_exception(args):
    _crash_logger.error(
        "Unhandled exception on background thread %r",
        args.thread.name if args.thread else "?",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def _heartbeat():
    _crash_logger.info("Still running")
    timer = threading.Timer(HEARTBEAT_INTERVAL_SECONDS, _heartbeat)
    timer.daemon = True
    timer.start()


def install_crash_logging():
    """Call once at startup. Covers the three ways an idle --windowed app can
    disappear without a trace today:

    - An uncaught exception on the main thread: sys.excepthook's default
      traceback print has no console to write to in a --windowed build, so
      it's silently swallowed. Redirected into the wrapper log instead.
    - An uncaught exception on a background thread (e.g. the Streamlit
      bootstrap thread from streamlit_runner.py): same problem, via
      threading.excepthook (Python 3.8+).
    - A fatal native crash (segfault, abort, etc. -- e.g. from a native
      library going idle/suspended and misbehaving on resume): faulthandler
      normally dumps a traceback to stderr, which again goes nowhere here,
      so it's pointed at its own file under the data dir instead (opened for
      the life of the process, since faulthandler needs a real, already-open
      file object to dump to from a signal handler).

    None of these three catch a hard `kill`/OOM-kill of the whole process, so
    a periodic heartbeat is also logged -- if the app vanishes between two
    heartbeats with no exception or faulthandler entry, that's itself the
    signal that something outside Python's control (OS-level kill, power
    event, etc.) ended the process.
    """
    sys.excepthook = _log_uncaught_exception
    threading.excepthook = _log_uncaught_thread_exception

    crash_log_path = get_data_dir() / CRASH_LOG_FILENAME
    crash_log_file = open(crash_log_path, "a", encoding="utf-8")
    faulthandler.enable(file=crash_log_file, all_threads=True)
    atexit.register(crash_log_file.close)

    _heartbeat()
