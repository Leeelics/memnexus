"""Storage backends for Session Explorer."""

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC
from pathlib import Path

from memnexus.session.models import (
    DecisionFingerprint,
    ExplorationRecord,
    StorageError,
)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_fingerprint(self, fingerprint: DecisionFingerprint) -> None:
        """Save a decision fingerprint."""
        pass

    @abstractmethod
    def get_fingerprint(self, hash_str: str) -> DecisionFingerprint | None:
        """Get a fingerprint by hash."""
        pass

    @abstractmethod
    def get_all_fingerprints(self) -> dict[str, DecisionFingerprint]:
        """Get all fingerprints."""
        pass

    @abstractmethod
    def save_exploration(self, record: ExplorationRecord) -> None:
        """Save an exploration record."""
        pass

    @abstractmethod
    def get_exploration(self, session_id: str) -> ExplorationRecord | None:
        """Get exploration record for a session."""
        pass

    @abstractmethod
    def get_all_explorations(self) -> dict[str, ExplorationRecord]:
        """Get all exploration records."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close storage connection."""
        pass


class JSONStorage(StorageBackend):
    """JSON file-based storage for development."""

    def __init__(self, storage_path: Path | str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.fingerprints_file = self.storage_path / "fingerprints.json"
        self.explorations_file = self.storage_path / "explorations.json"

        # Initialize files if they don't exist
        if not self.fingerprints_file.exists():
            self._save_json(self.fingerprints_file, {"fingerprints": {}, "metadata": {}})
        if not self.explorations_file.exists():
            self._save_json(self.explorations_file, {"explorations": {}})

    def _load_json(self, file_path: Path) -> dict:
        """Load JSON from file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise StorageError(f"Failed to load {file_path}: {e}")

    def _save_json(self, file_path: Path, data: dict) -> None:
        """Save JSON to file atomically."""
        try:
            temp_file = file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.rename(file_path)
        except Exception as e:
            raise StorageError(f"Failed to save {file_path}: {e}")

    def save_fingerprint(self, fingerprint: DecisionFingerprint) -> None:
        data = self._load_json(self.fingerprints_file)
        data["fingerprints"][fingerprint.hash] = {
            "hash": fingerprint.hash,
            "keywords": fingerprint.keywords,
            "timestamp": fingerprint.timestamp,
            "source_session": fingerprint.source_session,
            "content_preview": fingerprint.content_preview,
        }
        data["metadata"]["updated_at"] = datetime.now(UTC).isoformat()
        self._save_json(self.fingerprints_file, data)

    def get_fingerprint(self, hash_str: str) -> DecisionFingerprint | None:
        data = self._load_json(self.fingerprints_file)
        fp_data = data["fingerprints"].get(hash_str)
        if not fp_data:
            return None
        return DecisionFingerprint(**fp_data)

    def get_all_fingerprints(self) -> dict[str, DecisionFingerprint]:
        data = self._load_json(self.fingerprints_file)
        return {k: DecisionFingerprint(**v) for k, v in data["fingerprints"].items()}

    def save_exploration(self, record: ExplorationRecord) -> None:
        data = self._load_json(self.explorations_file)
        data["explorations"][record.session_id] = {
            "session_id": record.session_id,
            "explored_by": record.explored_by,
            "explored_at": record.explored_at,
            "relevance_score": record.relevance_score,
            "decisions_extracted": record.decisions_extracted,
        }
        self._save_json(self.explorations_file, data)

    def get_exploration(self, session_id: str) -> ExplorationRecord | None:
        data = self._load_json(self.explorations_file)
        rec_data = data["explorations"].get(session_id)
        if not rec_data:
            return None
        return ExplorationRecord(**rec_data)

    def get_all_explorations(self) -> dict[str, ExplorationRecord]:
        data = self._load_json(self.explorations_file)
        return {k: ExplorationRecord(**v) for k, v in data["explorations"].items()}

    def close(self) -> None:
        pass  # JSON storage doesn't need explicit close


class SQLiteStorage(StorageBackend):
    """SQLite-based storage for production."""

    def __init__(self, storage_path: Path | str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.db_path = self.storage_path / "explorer.db"
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fingerprints (
                    hash TEXT PRIMARY KEY,
                    keywords TEXT,
                    timestamp TEXT,
                    source_session TEXT,
                    content_preview TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS explorations (
                    session_id TEXT PRIMARY KEY,
                    explored_by TEXT,
                    explored_at TEXT,
                    relevance_score REAL,
                    decisions_extracted INTEGER
                )
            """)
            conn.commit()

    def _dict_to_fingerprint(self, row: tuple) -> DecisionFingerprint:
        """Convert database row to DecisionFingerprint."""
        return DecisionFingerprint(
            hash=row[0],
            keywords=json.loads(row[1]),
            timestamp=row[2],
            source_session=row[3],
            content_preview=row[4],
        )

    def _dict_to_exploration(self, row: tuple) -> ExplorationRecord:
        """Convert database row to ExplorationRecord."""
        return ExplorationRecord(
            session_id=row[0],
            explored_by=row[1],
            explored_at=row[2],
            relevance_score=row[3],
            decisions_extracted=row[4],
        )

    def save_fingerprint(self, fingerprint: DecisionFingerprint) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fingerprints
                    (hash, keywords, timestamp, source_session, content_preview)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        fingerprint.hash,
                        json.dumps(fingerprint.keywords),
                        fingerprint.timestamp,
                        fingerprint.source_session,
                        fingerprint.content_preview,
                    ),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save fingerprint: {e}")

    def get_fingerprint(self, hash_str: str) -> DecisionFingerprint | None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM fingerprints WHERE hash = ?", (hash_str,))
                row = cursor.fetchone()
                if row:
                    return self._dict_to_fingerprint(row)
                return None
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get fingerprint: {e}")

    def get_all_fingerprints(self) -> dict[str, DecisionFingerprint]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM fingerprints")
                return {row[0]: self._dict_to_fingerprint(row) for row in cursor.fetchall()}
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get fingerprints: {e}")

    def save_exploration(self, record: ExplorationRecord) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO explorations
                    (session_id, explored_by, explored_at, relevance_score, decisions_extracted)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record.session_id,
                        record.explored_by,
                        record.explored_at,
                        record.relevance_score,
                        record.decisions_extracted,
                    ),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save exploration: {e}")

    def get_exploration(self, session_id: str) -> ExplorationRecord | None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM explorations WHERE session_id = ?", (session_id,)
                )
                row = cursor.fetchone()
                if row:
                    return self._dict_to_exploration(row)
                return None
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get exploration: {e}")

    def get_all_explorations(self) -> dict[str, ExplorationRecord]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM explorations")
                return {row[0]: self._dict_to_exploration(row) for row in cursor.fetchall()}
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get explorations: {e}")

    def close(self) -> None:
        pass  # SQLite connections are context-managed


def create_storage(
    storage_path: Path | str,
    backend: str = "auto",
) -> StorageBackend:
    """Create appropriate storage backend.

    Args:
        storage_path: Path to storage directory
        backend: "sqlite", "json", or "auto" (default: sqlite)

    Returns:
        StorageBackend instance
    """
    if backend == "auto":
        backend = "sqlite"  # Default to SQLite for production

    if backend == "sqlite":
        return SQLiteStorage(storage_path)
    elif backend == "json":
        return JSONStorage(storage_path)
    else:
        raise ConfigurationError(f"Unknown storage backend: {backend}")


# Import needed for JSONStorage
from datetime import datetime  # noqa: E402

from memnexus.session.models import ConfigurationError  # noqa: E402
