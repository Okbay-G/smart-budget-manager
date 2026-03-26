"""SQLite-based repository layer for data persistence.

MVP3: Account repository for CRUD operations on accounts.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, TypeVar

from ..domain.models import Account

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common helper methods."""

    def __init__(self, db) -> None:
        self.db = db

    def _next_id(self, existing_ids: Iterable[int]) -> int:
        """Calculate next available ID."""
        ids = list(existing_ids)
        return (max(ids) + 1) if ids else 1


class SqliteAccountRepository(BaseRepository[Account]):
    """Repository for managing account persistence in SQLite."""

    def list_all(self, user_id: int) -> List[Account]:
        """Retrieve all accounts for a user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM accounts WHERE user_id = ? ORDER BY name", (user_id,))
        return [Account(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def add(self, user_id: int, name: str) -> Account:
        """Create new account for a user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (user_id, name) VALUES (?, ?)", (user_id, name.strip()))
        conn.commit()
        return Account(id=cursor.lastrowid, name=name.strip())

    def get_by_id(self, user_id: int, account_id: int) -> Optional[Account]:
        """Retrieve account by ID for a user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
        row = cursor.fetchone()
        if row:
            return Account(id=row[0], name=row[1])
        return None

    def rename(self, user_id: int, account_id: int, new_name: str) -> None:
        """Rename existing account for a user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE accounts SET name = ? WHERE id = ? AND user_id = ?",
            (new_name.strip(), account_id, user_id)
        )
        conn.commit()

    def delete(self, user_id: int, account_id: int) -> None:
        """Delete account for a user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
        conn.commit()
