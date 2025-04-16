import sqlite3

def setup_database(db_file):
    """Sets up the database for storing game data."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create a table for storing player stats
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name TEXT NOT NULL,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        role TEXT
    )
    """)

    conn.commit()
    conn.close()
