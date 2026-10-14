# Database Migrations

MAVEN stores every project's data in local SQLite files: a shared `maven.db` listing all projects, plus a `<project>_tier1.db` and `<project>_tier2.db` per project. The columns in those files (which datasheet questions exist, which tier2/master fields exist) are decided by whatever MAVEN version created them. When a newer MAVEN release adds a new question or field, old project files on a user's machine need to pick up that change automatically, without the user re-creating the project.

This is handled by `maven/migrations.py`.

## How it works

Every db file carries its own schema version in SQLite's built-in `PRAGMA user_version` field — a single integer stored in the file itself, invisible to normal table listings. There's no separate version table to create or exclude from queries.

Alongside that, `maven/migrations.py` keeps an ordered list of upgrade steps per kind of db file (`"master"`, `"tier1"`, `"tier2"`). Each step is a small Python function that runs plain SQL against the raw `sqlite3.Connection` (e.g. "add this column"). The current version for a kind is just `len(MIGRATIONS[kind]) + 1` — the schema shipped in a given release is implicitly "version 1," and every migration appended after that bumps the target version by one. Nothing needs to be hand-counted or kept in sync separately.

Whenever MAVEN opens a db file (`get_db()` in `maven/app.py`), it checks the file's `PRAGMA user_version` against the current version for that kind:

- If the file is already current, nothing happens.
- If the file is behind, every pending step between its version and the current version runs in order, automatically. The user never sees this — same experience as opening a document in a newer version of a word processor and having it transparently upgrade the file format.
- Each step runs inside its own transaction (`BEGIN IMMEDIATE` ... step ... bump version ... `COMMIT`). If a step fails partway through, the whole transaction rolls back and the version is left exactly where it was — there's no half-upgraded state. The file is either fully at version N or fully at version N-1, never in between.

Brand-new project files skip this process entirely: `create_master_db()`, `create_tier1_db()`, and `create_tier2_db()` stamp a freshly created file at the current version the moment its tables are built, so new projects are always born current and never run migration steps.

Legacy files that predate this system (version `0`, since `PRAGMA user_version` defaults to `0` on any sqlite file) are treated as already matching the version-1 baseline — version 1 is defined as "whatever schema MAVEN was shipping right before this versioning system existed," so no migration step is needed to get there.

## Adding a migration

When a future release adds a new datasheet question, tier2 field, or master-table column:

1. Make the normal code/config change (e.g. add the question to `maven/metadata_template/datasheet_sections.yaml`). This already makes *new* projects get the column — unchanged from today.
2. In `maven/migrations.py`, append one function to the relevant list in `MIGRATIONS`:

   ```python
   def _add_new_field(con):
       con.execute("ALTER TABLE datasheet ADD COLUMN new_field VARCHAR DEFAULT ''")

   MIGRATIONS["tier1"].append(_add_new_field)
   ```

3. That's it. The target version for that kind increments automatically, and every existing project file picks up the new column the next time it's opened — atomically, with no user-visible action and no change needed anywhere else in the codebase.

## Key pieces

| Piece | Location | Purpose |
|---|---|---|
| `MIGRATIONS` | `maven/migrations.py` | Per-kind ordered list of upgrade-step functions |
| `current_version(kind)` | `maven/migrations.py` | Derives the target version from `len(MIGRATIONS[kind]) + 1` |
| `detect_kind(db_path)` | `maven/migrations.py` | Maps a filename to `"master"` / `"tier1"` / `"tier2"` / `None` (unrelated files are skipped) |
| `ensure_schema_current(con, db_path)` | `maven/migrations.py` | The migration runner, called on every db open |
| `stamp_current_version(con, kind)` | `maven/migrations.py` | Marks a brand-new file as already current |
| `get_db()` | `maven/app.py` | Calls `ensure_schema_current()` on every open |
| `create_master_db()` / `create_tier1_db()` / `create_tier2_db()` | `maven/app.py` | Call `stamp_current_version()` right after building a new file's tables |

## Tests

`tests/test_migrations.py` covers: kind detection, a fresh file being a no-op, stamping a new file, a legacy (version-0) file landing on the current version, a pending migration applying and bumping the version, and a failing migration rolling back cleanly with the version left unchanged.

Run with:

```
pytest tests/test_migrations.py
```
