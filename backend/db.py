import sqlite3
from flask import g

from config import get_database_path

def get_db():
    database = get_database_path()
    print("Using DB at:", database)
    if "db" not in g:
        g.db = sqlite3.connect(
            database,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
