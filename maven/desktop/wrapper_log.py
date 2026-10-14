"""Shared JSON-Lines logger for the desktop wrapper (startup, self-update,
menu actions). The Streamlit app's own logic keeps using Streamlit/print
output -- this is only for the wrapper code that has no visible stdout once
packaged as a --windowed PyInstaller build.

Each line in <data_dir>/wrapper.log is one JSON object. Call get_logger(name)
from any desktop module to get a child logger that feeds the one shared file
handler below.
"""
import json
import logging
from datetime import datetime, timezone

from maven.desktop.paths import get_data_dir

LOG_FILENAME = "wrapper.log"

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


def export_logs(dest_path):
    records = read_records()
    dest_path = str(dest_path)
    if dest_path.lower().endswith(".json"):
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    else:
        with open(dest_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(
                    f"{record.get('timestamp', '')} {record.get('level', '')} "
                    f"{record.get('message', '')}\n"
                )
