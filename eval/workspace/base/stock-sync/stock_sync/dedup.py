"""Remembers which events were already sent, so a re-delivered event is not sent twice.

The broker re-delivers events after a restart (offsets are committed after the send), so
this store is what prevents duplicate partner calls. Keyed on the event id only.
"""
import sqlite3


class SentLog:
    def __init__(self, path):
        self._db = sqlite3.connect(path)
        self._db.execute("CREATE TABLE IF NOT EXISTS sent (event_id TEXT PRIMARY KEY)")

    def seen(self, event_id):
        cur = self._db.execute("SELECT 1 FROM sent WHERE event_id = ?", (event_id,))
        return cur.fetchone() is not None

    def mark(self, event_id):
        self._db.execute("INSERT OR IGNORE INTO sent (event_id) VALUES (?)", (event_id,))
        self._db.commit()
