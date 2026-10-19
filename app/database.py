import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

DB_PATH = Path("data/chat_history.sqlite3")


def get_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db() -> None:
    """
    Initialize SQLite tables for authentication and conversation history.

    Long-term and episodic memories are stored in ChromaDB, not SQLite.
    """
    with get_connection() as connection:
        tables = {row["name"] for row in connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """).fetchall()}

        # Preserve the original messages table if it uses
        # the old session_id-based schema.
        if "messages" in tables:
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(messages)").fetchall()
            }

            if "conversation_id" not in columns:
                if "legacy_messages" in tables:
                    raise RuntimeError(
                        "Both old messages and legacy_messages exist. "
                        "Inspect the database before migrating."
                    )

                connection.execute("ALTER TABLE messages RENAME TO legacy_messages")

        # User accounts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                is_email_verified INTEGER NOT NULL DEFAULT 0
                    CHECK (is_email_verified IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

        # One active email-verification token per user
        connection.execute("""
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                user_id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            )
            """)

        # Conversations belong to authenticated users
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT 'New conversation',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            )
            """)

        # Each message belongs to one conversation
        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id) ON DELETE CASCADE
            )
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations(user_id, updated_at)
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, id)
            """)


def create_conversation(user_id: str) -> dict:
    """Create a conversation for a user and return its details."""
    conversation_id = str(uuid4())

    with closing(get_connection()) as connection, connection:
        connection.execute(
            """
            INSERT INTO conversations (id, user_id)
            VALUES (?, ?)
            """,
            (conversation_id, user_id),
        )

        row = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()

    return dict(row)


def list_conversations(user_id: str) -> list[dict]:
    """Return a user's conversations, newest activity first."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_conversation_for_user(
    conversation_id: str,
    user_id: str,
):
    """Return a conversation only if it belongs to the given user."""
    with closing(get_connection()) as connection:
        return connection.execute(
            """
            SELECT id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()


def get_conversation_messages(
    conversation_id: str,
) -> list[dict]:
    """Return all messages in a conversation, in chronological order."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_recent_messages(
    conversation_id: str,
    limit: int = 20,
) -> list[dict]:
    """Return the most recent messages in chronological order."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, limit),
        ).fetchall()

    return [dict(row) for row in reversed(rows)]


def save_exchange(
    conversation_id: str,
    user_message: str,
    assistant_message: str,
) -> None:
    """Save a user message and assistant reply in one transaction."""
    with closing(get_connection()) as connection, connection:
        existing_messages = connection.execute(
            """
            SELECT COUNT(*) AS message_count
            FROM messages
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

        connection.executemany(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            [
                (conversation_id, "user", user_message),
                (conversation_id, "assistant", assistant_message),
            ],
        )

        # Use the first user message as the initial chat title.
        if existing_messages["message_count"] == 0:
            title = " ".join(user_message.split())[:60]

            connection.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title or "New conversation", conversation_id),
            )
        else:
            connection.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (conversation_id,),
            )


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DB_PATH.resolve()}")
