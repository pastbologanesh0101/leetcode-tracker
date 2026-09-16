import os
import sqlite3
from datetime import datetime, timedelta

from flask import Flask, g


def get_db():
    """Return a request-scoped SQLite connection."""
    from flask import current_app

    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS problem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    topic TEXT,
    status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'attempted', 'solved')),
    notes TEXT,
    date_solved TEXT,
    created_at TEXT NOT NULL
);
"""


def init_db(app):
    db_path = app.config["DATABASE"]
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def create_app(testing=False, database=None):
    """Application factory.

    testing=True wires up an in-memory SQLite database so tests never
    touch a real file on disk.
    """
    app = Flask(__name__)

    if testing:
        app.config["TESTING"] = True
        app.config["DATABASE"] = database or ":memory:"
        app.config["WTF_CSRF_ENABLED"] = False
    else:
        instance_dir = os.path.join(app.root_path, "..", "instance")
        app.config["DATABASE"] = database or os.path.join(instance_dir, "leetcode_tracker.db")

    app.config["SECRET_KEY"] = "dev-secret-key-not-for-production"

    if app.config["DATABASE"] == ":memory:" or testing:
        # For in-memory / test DBs we keep a single persistent connection on
        # the app so every request in the test client sees the same schema.
        conn = sqlite3.connect(app.config["DATABASE"], check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        conn.commit()
        app._test_db_conn = conn

        def get_test_db():
            return app._test_db_conn

        app.get_db = get_test_db
    else:
        init_db(app)
        app.get_db = lambda: get_db()
        app.teardown_appcontext(close_db)

    from app.routes import bp

    app.register_blueprint(bp)

    return app
