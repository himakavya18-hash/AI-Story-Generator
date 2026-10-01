"""SQLite storage for generated stories, favorites, and app settings."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "story_generator.db"


def _connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def _database():
    """Yield a database connection and always close it after committing."""
    connection = _connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the application's tables when they do not already exist."""
    with _database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                story TEXT NOT NULL,
                audio_url TEXT,
                video_url TEXT,
                is_favorite INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("tts_rate", "175"),
        )


def save_story(
    prompt: str, story: str, audio_url: str | None, video_url: str | None
) -> int:
    """Save one generated story and return its database ID."""
    with _database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO stories (prompt, story, audio_url, video_url)
            VALUES (?, ?, ?, ?)
            """,
            (prompt, story, audio_url, video_url),
        )
        return int(cursor.lastrowid)


def get_stories(*, favorites_only: bool = False, limit: int | None = None) -> list[dict]:
    """Return newest stories first, optionally returning favorites only."""
    query = "SELECT * FROM stories"
    if favorites_only:
        query += " WHERE is_favorite = 1"
    query += " ORDER BY id DESC"
    parameters: tuple[int, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        parameters = (limit,)

    with _database() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]


def toggle_favorite(story_id: int) -> None:
    """Switch a story between favorite and non-favorite."""
    with _database() as connection:
        connection.execute(
            """
            UPDATE stories
            SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (story_id,),
        )


def get_tts_rate() -> int:
    with _database() as connection:
        row = connection.execute(
            "SELECT value FROM settings WHERE key = ?", ("tts_rate",)
        ).fetchone()
    return int(row["value"]) if row else 175


def set_tts_rate(rate: int) -> None:
    if not 100 <= rate <= 250:
        raise ValueError("Narration speed must be between 100 and 250")
    with _database() as connection:
        connection.execute(
            "UPDATE settings SET value = ? WHERE key = ?", (str(rate), "tts_rate")
        )
