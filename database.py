import sqlite3
from contextlib import contextmanager

DB_PATH = "bot.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                status TEXT DEFAULT 'pending',
                language TEXT DEFAULT 'ru',
                current_lesson INTEGER DEFAULT 0,
                awaiting TEXT DEFAULT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS lessons_cache (
                lesson_number INTEGER,
                language TEXT,
                content TEXT,
                PRIMARY KEY (lesson_number, language)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS quiz_cache (
                quiz_key TEXT PRIMARY KEY,
                content TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                test_type TEXT,
                lesson_range TEXT,
                score INTEGER,
                total INTEGER,
                status TEXT DEFAULT 'pending'
            )
        """)


def add_user(user_id, full_name, username):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, full_name, username) VALUES (?, ?, ?)",
            (user_id, full_name, username),
        )


def get_user(user_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def set_status(user_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE users SET status=? WHERE user_id=?", (status, user_id))


def set_language(user_id, language):
    with get_conn() as conn:
        conn.execute("UPDATE users SET language=? WHERE user_id=?", (language, user_id))


def set_current_lesson(user_id, lesson_number):
    with get_conn() as conn:
        conn.execute("UPDATE users SET current_lesson=? WHERE user_id=?", (lesson_number, user_id))


def set_awaiting(user_id, awaiting):
    with get_conn() as conn:
        conn.execute("UPDATE users SET awaiting=? WHERE user_id=?", (awaiting, user_id))


def get_pending_users():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users WHERE status='pending'").fetchall()
        return [dict(r) for r in rows]


def get_cached_lesson(lesson_number, language):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT content FROM lessons_cache WHERE lesson_number=? AND language=?",
            (lesson_number, language),
        ).fetchone()
        return row["content"] if row else None


def save_lesson(lesson_number, language, content):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO lessons_cache (lesson_number, language, content) VALUES (?, ?, ?)",
            (lesson_number, language, content),
        )


def get_cached_quiz(quiz_key):
    with get_conn() as conn:
        row = conn.execute("SELECT content FROM quiz_cache WHERE quiz_key=?", (quiz_key,)).fetchone()
        return row["content"] if row else None


def save_quiz(quiz_key, content):
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO quiz_cache (quiz_key, content) VALUES (?, ?)", (quiz_key, content))


def add_test_result(user_id, test_type, lesson_range, score, total):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO test_results (user_id, test_type, lesson_range, score, total) VALUES (?, ?, ?, ?, ?)",
            (user_id, test_type, lesson_range, score, total),
        )
        return cur.lastrowid


def get_test_result(result_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM test_results WHERE id=?", (result_id,)).fetchone()
        return dict(row) if row else None


def set_test_status(result_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE test_results SET status=? WHERE id=?", (status, result_id))