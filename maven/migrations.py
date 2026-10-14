"""Schema versioning for MAVEN's SQLite project databases.

Each db file (maven.db, <project>_tier1.db, <project>_tier2.db) carries its
own schema version in SQLite's built-in `PRAGMA user_version`. Bumping the
app's shipped schema means appending one upgrade-step function to the
relevant list in MIGRATIONS below; CURRENT_VERSION is derived from the list
length, so there is nothing else to keep in sync.
"""
import sqlite3
from typing import Callable, Dict, List, Optional

# Ordered upgrade steps per db kind. Step i (0-indexed) upgrades a file from
# version i+1 to version i+2. Start empty: the schema shipped in this release
# is version 1 for every kind, with no steps required to reach it.
MIGRATIONS: Dict[str, List[Callable[[sqlite3.Connection], None]]] = {
    "master": [],
    "tier1": [],
    "tier2": [],
}

# Table whose presence marks "this file's base schema already exists",
# distinguishing a freshly-created (still-empty) file from one that's ready
# to be checked/migrated.
MARKER_TABLE: Dict[str, str] = {
    "master": "projects",
    "tier1": "datasheet",
    "tier2": "data_and_hpc_info",
}


def current_version(kind: str) -> int:
    return len(MIGRATIONS[kind]) + 1


def detect_kind(db_path: str) -> Optional[str]:
    name = db_path.replace("\\", "/").rsplit("/", 1)[-1]
    if name == "maven.db":
        return "master"
    if name.endswith("_tier1.db"):
        return "tier1"
    if name.endswith("_tier2.db"):
        return "tier2"
    return None


def _table_exists(con: sqlite3.Connection, table_name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    return row is not None


def _get_user_version(con: sqlite3.Connection) -> int:
    return con.execute("PRAGMA user_version").fetchone()[0]


def _set_user_version(con: sqlite3.Connection, version: int) -> None:
    con.execute(f"PRAGMA user_version = {int(version)}")


def stamp_current_version(con: sqlite3.Connection, kind: str) -> None:
    _set_user_version(con, current_version(kind))
    con.commit()


def ensure_schema_current(con: sqlite3.Connection, db_path: str) -> None:
    kind = detect_kind(db_path)
    if kind is None:
        return

    if not _table_exists(con, MARKER_TABLE[kind]):
        # File is mid-creation; its create_*_db() caller will stamp the
        # version explicitly once the base schema is in place.
        return

    target = current_version(kind)
    version = _get_user_version(con)
    if version >= target:
        return

    # Version 0 covers both brand-new legacy files (predating this system)
    # and files whose base schema matches today's version-1 baseline; treat
    # it as already at version 1 with no step to run.
    if version == 0:
        version = 1
        _set_user_version(con, version)
        con.commit()

    steps = MIGRATIONS[kind]
    for v in range(version, target):
        step = steps[v - 1]
        try:
            con.execute("BEGIN IMMEDIATE")
            step(con)
            _set_user_version(con, v + 1)
            con.commit()
        except Exception:
            con.rollback()
            raise
