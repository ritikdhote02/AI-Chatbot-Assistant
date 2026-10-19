import re
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

DB_PATH = Path("data/chat_history.sqlite3")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                source_message_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE,

                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id) ON DELETE CASCADE
            )
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_user
            ON episodic_memories(user_id, updated_at)
            """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                memory_key TEXT NOT NULL,
                memory_value TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'fact',
                source_conversation_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (source_conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE SET NULL,

                UNIQUE (user_id, memory_key)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_long_term_memories_user
            ON long_term_memories(user_id, updated_at)
        """)


def create_conversation(user_id: str) -> dict:
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
):
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


def save_episodic_memory(
    user_id: str,
    conversation_id: str,
    title: str,
    summary: str,
    source_message_count: int,
) -> dict:
    episode_id = str(uuid4())

    with closing(get_connection()) as connection, connection:
        connection.execute(
            """
            INSERT INTO episodic_memories (
                id,
                user_id,
                conversation_id,
                title,
                summary,
                source_message_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                title = excluded.title,
                summary = excluded.summary,
                source_message_count = excluded.source_message_count,
                updated_at = CURRENT_TIMESTAMP
            WHERE episodic_memories.user_id = excluded.user_id
            """,
            (
                episode_id,
                user_id,
                conversation_id,
                title,
                summary,
                source_message_count,
            ),
        )

        row = connection.execute(
            """
            SELECT id, user_id, conversation_id, title,
                   summary, source_message_count,
                   created_at, updated_at
            FROM episodic_memories
            WHERE conversation_id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()

        if row is None:
            raise RuntimeError("Could not save episodic memory.")

    return dict(row)


def list_episodic_memories(user_id: str) -> list[dict]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, conversation_id, title, summary,
                   source_message_count, created_at, updated_at
            FROM episodic_memories
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_relevant_episodic_memories(
    user_id: str,
    query: str,
    limit: int = 3,
) -> list[dict]:
    # A lightweight keyword retriever for our first version.
    # Later, we'll be able to replace it with semantic retrieval.
    stop_words = {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "from",
        "what",
        "when",
        "where",
        "have",
        "has",
        "had",
        "was",
        "were",
        "are",
        "you",
        "your",
        "our",
        "about",
        "into",
        "how",
        "did",
        "does",
        "can",
        "could",
        "would",
        "should",
        "been",
        "being",
        "not",
        "but",
        "then",
        "than",
    }

    def tokenize(value: str) -> set[str]:
        return {
            word
            for word in re.findall(r"[a-z0-9]+", value.lower())
            if len(word) > 2 and word not in stop_words
        }

    query_words = tokenize(query)

    if not query_words:
        return []

    # Bound the amount of data loaded for simple retrieval.
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, conversation_id, title, summary,
                   source_message_count, created_at, updated_at
            FROM episodic_memories
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 100
            """,
            (user_id,),
        ).fetchall()

    scored = []

    for row in rows:
        episode = dict(row)
        episode_words = tokenize(episode["title"] + " " + episode["summary"])

        overlap = query_words & episode_words

        if overlap:
            # Rank by proportion of query terms that match.
            score = len(overlap) / len(query_words)
            scored.append((score, episode))

    scored.sort(
        key=lambda item: (
            item[0],
            item[1]["updated_at"],
        ),
        reverse=True,
    )

    return [episode for _, episode in scored[:limit]]


def save_long_term_memory(
    user_id: str,
    memory_key: str,
    memory_value: str,
    category: str = "fact",
    source_conversation_id: str | None = None,
) -> dict:
    memory_id = str(uuid4())

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO long_term_memories (
                id,
                user_id,
                memory_key,
                memory_value,
                category,
                source_conversation_id
            )
            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id, memory_key)
            DO UPDATE SET
                memory_value = excluded.memory_value,
                category = excluded.category,
                source_conversation_id =
                    excluded.source_conversation_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                memory_id,
                user_id,
                memory_key,
                memory_value,
                category,
                source_conversation_id,
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM long_term_memories
            WHERE user_id = ? AND memory_key = ?
            """,
            (user_id, memory_key),
        ).fetchone()

        return dict(row)


def list_long_term_memories(user_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM long_term_memories
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def update_long_term_memory(
    user_id: str,
    memory_id: str,
    memory_value: str,
    category: str,
) -> dict | None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE long_term_memories
            SET memory_value = ?,
                category = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (memory_value, category, memory_id, user_id),
        )

        row = connection.execute(
            """
            SELECT *
            FROM long_term_memories
            WHERE id = ? AND user_id = ?
            """,
            (memory_id, user_id),
        ).fetchone()

        return dict(row) if row else None


def delete_long_term_memory(
    user_id: str,
    memory_id: str,
) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM long_term_memories
            WHERE id = ? AND user_id = ?
            """,
            (memory_id, user_id),
        )

        return cursor.rowcount > 0


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DB_PATH.resolve()}")
