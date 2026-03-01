"""
Run this ONCE to migrate your existing SQLite database.
It safely adds any missing columns without touching existing data.

Usage:
    python migrate_db.py
"""

import sqlite3
import os

# ── Find your DB file ─────────────────────────────────────────────────────────
# Adjust this path if your DB is named differently or in a different folder.
DB_PATH = os.path.join(os.path.dirname(__file__), "studentassist.db")

# Common alternative paths — script tries each in order
CANDIDATE_PATHS = [
    DB_PATH,
    os.path.join(os.path.dirname(__file__), "app", "studentassist.db"),
    os.path.join(os.path.dirname(__file__), "backend", "studentassist.db"),
    os.path.join(os.path.dirname(__file__), "data", "studentassist.db"),
    os.path.join(os.path.dirname(__file__), "db", "studentassist.db"),
    "studentassist.db",
    "app.db",
    "database.db",
]

def find_db() -> str:
    for p in CANDIDATE_PATHS:
        if os.path.exists(p):
            print(f"[migrate] Found DB at: {p}")
            return p
    raise FileNotFoundError(
        "Could not find your SQLite database file.\n"
        "Please set DB_PATH at the top of this script to the correct path."
    )


# ── Columns to add per table ──────────────────────────────────────────────────
# Format: (table_name, column_name, column_definition)
MIGRATIONS = [
    # assessment_results
    ("assessment_results", "attempt_number",  "INTEGER NOT NULL DEFAULT 1"),
    ("assessment_results", "total_score",     "REAL NOT NULL DEFAULT 0.0"),
    ("assessment_results", "percentage",      "REAL NOT NULL DEFAULT 0.0"),
    ("assessment_results", "section_scores",  "TEXT DEFAULT '{}' "),
    ("assessment_results", "weak_topics",     "TEXT DEFAULT '[]' "),
    ("assessment_results", "strong_topics",   "TEXT DEFAULT '[]' "),
    ("assessment_results", "difficulty_level","VARCHAR DEFAULT 'Beginner'"),
    ("assessment_results", "taken_at",        "DATETIME DEFAULT (datetime('now'))"),
    ("assessment_results", "exam_target",     "VARCHAR DEFAULT 'CAT'"),

    # students
    ("students", "has_taken_assessment", "BOOLEAN NOT NULL DEFAULT 0"),
    ("students", "exam_target",          "VARCHAR DEFAULT 'CAT'"),

    # mock_test_results
    ("mock_test_results", "exam_target",     "VARCHAR DEFAULT 'CAT'"),
    ("mock_test_results", "subject",         "VARCHAR DEFAULT ''"),
    ("mock_test_results", "topic",           "VARCHAR DEFAULT ''"),
    ("mock_test_results", "difficulty",      "VARCHAR DEFAULT 'Intermediate'"),
    ("mock_test_results", "total_questions", "INTEGER DEFAULT 0"),
    ("mock_test_results", "correct_answers", "INTEGER DEFAULT 0"),
    ("mock_test_results", "score",           "REAL DEFAULT 0.0"),
    ("mock_test_results", "grade",           "VARCHAR DEFAULT 'D'"),
    ("mock_test_results", "topic_breakdown", "TEXT DEFAULT '{}'"),
    ("mock_test_results", "taken_at",        "DATETIME DEFAULT (datetime('now'))"),

    # student_progress
    ("student_progress", "exam_target",  "VARCHAR DEFAULT 'CAT'"),
    ("student_progress", "subject",      "VARCHAR DEFAULT ''"),
    ("student_progress", "topic",        "VARCHAR DEFAULT ''"),
    ("student_progress", "attempts",     "INTEGER DEFAULT 0"),
    ("student_progress", "avg_score",    "REAL DEFAULT 0.0"),
    ("student_progress", "best_score",   "REAL DEFAULT 0.0"),
    ("student_progress", "last_score",   "REAL DEFAULT 0.0"),
    ("student_progress", "last_attempt", "DATETIME DEFAULT (datetime('now'))"),

    # weekly_logs
    ("weekly_logs", "exam_target",    "VARCHAR DEFAULT 'CAT'"),
    ("weekly_logs", "week_start",     "VARCHAR DEFAULT ''"),
    ("weekly_logs", "week_label",     "VARCHAR DEFAULT ''"),
    ("weekly_logs", "topics_covered", "TEXT DEFAULT '[]'"),
    ("weekly_logs", "total_hours",    "REAL DEFAULT 0.0"),
    ("weekly_logs", "summary_notes",  "TEXT DEFAULT ''"),
    ("weekly_logs", "updated_at",     "DATETIME DEFAULT (datetime('now'))"),

    # prep_schedules
    ("prep_schedules", "exam_target",  "VARCHAR DEFAULT 'CAT'"),
    ("prep_schedules", "plan_months",  "INTEGER DEFAULT 6"),
    ("prep_schedules", "start_date",   "VARCHAR DEFAULT ''"),
    ("prep_schedules", "exam_date",    "VARCHAR DEFAULT ''"),
    ("prep_schedules", "weeks",        "TEXT DEFAULT '[]'"),
    ("prep_schedules", "updated_at",   "DATETIME DEFAULT (datetime('now'))"),
]


def get_existing_columns(cursor, table: str) -> set:
    """Return the set of column names currently in `table`."""
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def get_existing_tables(cursor) -> set:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cursor.fetchall()}


def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    existing_tables = get_existing_tables(cursor)
    print(f"[migrate] Tables found: {sorted(existing_tables)}")

    added = []
    skipped = []
    missing_tables = []

    for table, column, definition in MIGRATIONS:
        if table not in existing_tables:
            missing_tables.append(table)
            continue

        existing_cols = get_existing_columns(cursor, table)
        if column in existing_cols:
            skipped.append(f"{table}.{column}")
            continue

        sql = f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        try:
            cursor.execute(sql)
            added.append(f"{table}.{column}")
            print(f"  [+] Added {table}.{column}")
        except sqlite3.OperationalError as e:
            print(f"  [!] Could not add {table}.{column}: {e}")

    conn.commit()
    conn.close()

    print("\n── Migration complete ──────────────────────────────")
    print(f"  Added  : {len(added)} column(s)")
    print(f"  Skipped: {len(skipped)} (already existed)")
    if missing_tables:
        unique_missing = sorted(set(missing_tables))
        print(f"  Missing tables (will be created by SQLAlchemy on next startup): {unique_missing}")
    print("────────────────────────────────────────────────────")
    print("\nNow restart your FastAPI server — the 500 errors should be gone.")


if __name__ == "__main__":
    db_path = find_db()
    migrate(db_path)
