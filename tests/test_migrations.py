import sqlite3

import pytest

from maven import migrations


def make_marker_db(tmp_path, filename, marker_table):
    path = tmp_path / filename
    con = sqlite3.connect(str(path))
    con.execute(f"CREATE TABLE {marker_table} (id INTEGER)")
    con.commit()
    return path, con


@pytest.mark.parametrize(
    "filename,kind",
    [
        ("maven.db", "master"),
        ("my_project_tier1.db", "tier1"),
        ("my_project_tier2.db", "tier2"),
        ("my_project.db", None),
    ],
)
def test_detect_kind(filename, kind):
    assert migrations.detect_kind(filename) == kind


def test_fresh_file_without_marker_table_is_noop(tmp_path):
    path = tmp_path / "my_project_tier1.db"
    con = sqlite3.connect(str(path))

    migrations.ensure_schema_current(con, str(path))

    assert con.execute("PRAGMA user_version").fetchone()[0] == 0
    con.close()


def test_stamp_current_version_sets_user_version(tmp_path):
    path, con = make_marker_db(tmp_path, "my_project_tier1.db", "datasheet")

    migrations.stamp_current_version(con, "tier1")

    assert con.execute("PRAGMA user_version").fetchone()[0] == migrations.current_version("tier1")
    con.close()


def test_legacy_file_with_marker_table_lands_on_current_version(tmp_path):
    path, con = make_marker_db(tmp_path, "my_project_tier2.db", "data_and_hpc_info")

    migrations.ensure_schema_current(con, str(path))

    assert con.execute("PRAGMA user_version").fetchone()[0] == migrations.current_version("tier2")
    con.close()


def test_pending_migration_runs_and_bumps_version(tmp_path, monkeypatch):
    path, con = make_marker_db(tmp_path, "my_project_tier1.db", "datasheet")
    con.execute("ALTER TABLE datasheet ADD COLUMN existing_col VARCHAR")
    con.execute("PRAGMA user_version = 1")
    con.commit()

    def add_new_field(c):
        c.execute("ALTER TABLE datasheet ADD COLUMN new_field VARCHAR DEFAULT ''")

    monkeypatch.setitem(migrations.MIGRATIONS, "tier1", [add_new_field])

    migrations.ensure_schema_current(con, str(path))

    cols = [row[1] for row in con.execute("PRAGMA table_info(datasheet)").fetchall()]
    assert "new_field" in cols
    assert con.execute("PRAGMA user_version").fetchone()[0] == 2
    con.close()


def test_failed_migration_rolls_back_and_leaves_version_unchanged(tmp_path, monkeypatch):
    path, con = make_marker_db(tmp_path, "my_project_tier1.db", "datasheet")
    con.execute("ALTER TABLE datasheet ADD COLUMN existing_col VARCHAR")
    con.execute("PRAGMA user_version = 1")
    con.commit()

    def broken_step(c):
        c.execute("ALTER TABLE datasheet ADD COLUMN new_field VARCHAR DEFAULT ''")
        raise RuntimeError("boom")

    monkeypatch.setitem(migrations.MIGRATIONS, "tier1", [broken_step])

    with pytest.raises(RuntimeError):
        migrations.ensure_schema_current(con, str(path))

    cols = [row[1] for row in con.execute("PRAGMA table_info(datasheet)").fetchall()]
    assert "new_field" not in cols
    assert con.execute("PRAGMA user_version").fetchone()[0] == 1
    con.close()
