"""SQLite-based repository layer for data persistence.

Provides repository classes for managing data persistence to SQLite.
Repositories implement the Data Access Object pattern, isolating database
operations from business logic.

Classes:
    BaseRepository: Abstract base repository with common helper methods.
    SqliteAccountRepository: Repository for account persistence.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, TypeVar

from ..domain.models import Account

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common helper methods.
    
    Provides foundation for all repository classes with ID generation
    and shared database connection handling.
    """

    def __init__(self, db) -> None:
        """Initialize repository with database connection.
        
        Args:
            db: Database connection manager.
        """
        self.db = db

    def _next_id(self, existing_ids: Iterable[int]) -> int:
        """Calculate next available ID.
        
        Args:
            existing_ids: Iterable of existing ID values.
            
        Returns:
            int: Next available ID (max + 1, or 1 if empty).
        """
        ids = list(existing_ids)
        return (max(ids) + 1) if ids else 1


class SqliteAccountRepository(BaseRepository[Account]):
    """Repository for managing account persistence in SQLite.
    
    Provides CRUD operations for user accounts with user isolation.
    """

    def list_all(self, user_id: int) -> List[Account]:
        """Retrieve all accounts for a user.
        
        Args:
            user_id (int): ID of user to filter by.
            
        Returns:
            List[Account]: List of user's accounts ordered by name.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM accounts WHERE user_id = ? ORDER BY name", (user_id,))
        return [Account(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def add(self, user_id: int, name: str) -> Account:
        """Create new account for a user.
        
        Args:
            user_id (int): ID of user creating the account.
            name (str): Account name (e.g., "Bank", "Cash").
            
        Returns:
            Account: Created account with assigned ID.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (user_id, name) VALUES (?, ?)", (user_id, name.strip()))
        conn.commit()
        return Account(id=cursor.lastrowid, name=name.strip())

    def get_by_id(self, user_id: int, account_id: int) -> Optional[Account]:
        """Retrieve account by ID for a user.
        
        Args:
            user_id (int): ID of user (for verification).
            account_id (int): ID of account to retrieve.
            
        Returns:
            Optional[Account]: Account if found, None otherwise.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
        row = cursor.fetchone()
        if row:
            return Account(id=row[0], name=row[1])
        return None

    def rename(self, user_id: int, account_id: int, new_name: str) -> None:
        """Rename existing account for a user.
        
        Args:
            user_id (int): ID of user (for verification).
            account_id (int): ID of account to rename.
            new_name (str): New account name.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE accounts SET name = ? WHERE id = ? AND user_id = ?",
            (new_name.strip(), account_id, user_id)
        )
        conn.commit()

    def delete(self, user_id: int, account_id: int) -> None:
        """Delete account for a user.
        
        Args:
            user_id (int): ID of user (for verification).
            account_id (int): ID of account to delete.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
        conn.commit()
