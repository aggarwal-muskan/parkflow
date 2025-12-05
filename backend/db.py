import sqlite3
from backend.config import Config


def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
