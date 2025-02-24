import sqlite3
from contextlib import contextmanager
from typing import Optional, Tuple
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self._init_db()

    def _init_db(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    user_id INTEGER PRIMARY KEY, 
                    total_donated INTEGER DEFAULT 0, 
                    total_entries INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def add_donation(self, user_id: int, amount: int) -> Tuple[int, int]:
        with self.get_connection() as conn:
            c = conn.cursor()
            new_entries = amount // Config.ENTRY_THRESHOLD

            c.execute("SELECT total_donated, total_entries FROM donations WHERE user_id = ?", (user_id,))
            row = c.fetchone()

            if row:
                total_donated, total_entries = row
                total_donated += amount
                total_entries += new_entries
                c.execute("UPDATE donations SET total_donated = ?, total_entries = ? WHERE user_id = ?",
                         (total_donated, total_entries, user_id))
            else:
                c.execute("INSERT INTO donations (user_id, total_donated, total_entries) VALUES (?, ?, ?)",
                         (user_id, amount, new_entries))

            conn.commit()
            return new_entries, total_entries if row else new_entries

    def add_manual_entries(self, user_id: int, entries: int) -> int:
        """Manually add entries for a user without requiring a donation."""
        with self.get_connection() as conn:
            c = conn.cursor()

            c.execute("SELECT total_entries FROM donations WHERE user_id = ?", (user_id,))
            row = c.fetchone()

            if row:
                total_entries = row[0] + entries
                c.execute("UPDATE donations SET total_entries = ? WHERE user_id = ?",
                         (total_entries, user_id))
            else:
                total_entries = entries
                c.execute("INSERT INTO donations (user_id, total_donated, total_entries) VALUES (?, ?, ?)",
                         (user_id, 0, entries))

            conn.commit()
            return total_entries

    def get_total_donations(self) -> int:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT SUM(total_donated) FROM donations")
            return c.fetchone()[0] or 0

    def get_user_entries(self, user_id: int) -> int:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT total_entries FROM donations WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            return result[0] if result else 0

    def get_user_total_donated(self, user_id: int) -> int:
        """Get the total amount donated by a user"""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT total_donated FROM donations WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            return result[0] if result else 0

    def get_all_entries(self) -> list:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, total_entries FROM donations")
            return c.fetchall()