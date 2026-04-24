"""SQLite-based repository layer for data persistence.

Provides CRUD operations for accounts, categories, transactions, and budgets.

Classes:
    BaseRepository: Abstract base repository with common helper methods.
    SqliteAccountRepository: Repository for account persistence.
    SqliteTransactionRepository: Repository for transaction persistence.
    SqliteCategoryRepository: Repository for category persistence.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, Iterable, List, Optional, TypeVar

from ..domain.models import Account, Transaction, TxType, Category, MonthlyBudget
from .db import Db

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common helper methods.
    
    Provides foundation for all repository classes with ID generation
    and shared database connection handling.
    """

    def __init__(self, db) -> None:
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


class SqliteTransactionRepository(BaseRepository[Transaction]):
    """Repository for managing transaction persistence.
    
    Provides CRUD operations for income and expense transactions.
    """

    def list_all(self, user_id: int) -> List[Transaction]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tx_type, account_id, category_id, amount, description, tx_date "
            "FROM transactions WHERE user_id = ? ORDER BY tx_date DESC",
            (user_id,)
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def list_for_month(self, user_id: int, year: int, month: int) -> List[Transaction]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tx_type, account_id, category_id, amount, description, tx_date "
            "FROM transactions WHERE user_id = ? "
            "AND CAST(strftime('%Y', tx_date) AS INTEGER) = ? "
            "AND CAST(strftime('%m', tx_date) AS INTEGER) = ? ORDER BY tx_date DESC",
            (user_id, year, month),
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def list_for_ytd(self, user_id: int, year: int, month: int) -> List[Transaction]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tx_type, account_id, category_id, amount, description, tx_date "
            "FROM transactions WHERE user_id = ? "
            "AND CAST(strftime('%Y', tx_date) AS INTEGER) = ? "
            "AND CAST(strftime('%m', tx_date) AS INTEGER) <= ? ORDER BY tx_date",
            (user_id, year, month),
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def add(self, user_id: int, tx: Transaction) -> Transaction:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (user_id, tx_type, account_id, category_id, amount, description, tx_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, tx.tx_type.value, tx.account_id, tx.category_id, tx.amount, tx.description, tx.tx_date),
        )
        conn.commit()
        return Transaction(
            id=cursor.lastrowid, tx_type=tx.tx_type, account_id=tx.account_id,
            category_id=tx.category_id, amount=tx.amount, description=tx.description, tx_date=tx.tx_date,
        )

    def replace_transaction(self, user_id: int, tx_id: int, new_tx: Transaction) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transactions SET tx_type = ?, account_id = ?, category_id = ?, "
            "amount = ?, description = ?, tx_date = ? WHERE id = ? AND user_id = ?",
            (new_tx.tx_type.value, new_tx.account_id, new_tx.category_id, new_tx.amount, new_tx.description, new_tx.tx_date, tx_id, user_id),
        )
        conn.commit()

    def delete(self, user_id: int, tx_id: int) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
        conn.commit()

    @staticmethod
    def _row_to_transaction(row: tuple) -> Transaction:
        return Transaction(
            id=row[0], tx_type=TxType(row[1]), account_id=row[2],
            category_id=row[3], amount=row[4], description=row[5],
            tx_date=datetime.strptime(row[6], "%Y-%m-%d").date(),
        )


class SqliteCategoryRepository(BaseRepository[Category]):
    """SQLite repository for Category entities."""

    def __init__(self, db: Db) -> None:
        self._db = db

    def add(self, user_id: int, name: str) -> Category:
        """Add a category for a user."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (user_id, name) VALUES (?, ?)",
            (user_id, name.strip())
        )
        conn.commit()
        cat_id = cursor.lastrowid
        return Category(id=cat_id, name=name.strip())

    def list_all(self, user_id: int) -> List[Category]:
        """List all categories for a user."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM categories WHERE user_id = ? ORDER BY name",
            (user_id,)
        )
        return [Category(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def get_by_id(self, user_id: int, category_id: int) -> Optional[Category]:
        """Get a specific category."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
            (category_id, user_id)
        )
        row = cursor.fetchone()
        return Category(id=row[0], name=row[1]) if row else None

    def rename(self, user_id: int, category_id: int, new_name: str) -> None:
        """Rename a category."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET name = ? WHERE id = ? AND user_id = ?",
            (new_name.strip(), category_id, user_id)
        )
        conn.commit()

    def delete(self, user_id: int, category_id: int) -> None:
        """Delete a category."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM categories WHERE id = ? AND user_id = ?",
            (category_id, user_id)
        )
        conn.commit()


class SqliteBudgetRepository(BaseRepository[MonthlyBudget]):
    """SQLite repository for MonthlyBudget entities."""

    def __init__(self, db: Db) -> None:
        self._db = db

    def add(self, user_id: int, category_id: int, year: int, month: int, limit_amount: float) -> MonthlyBudget:
        """Add a budget."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO monthly_budgets (user_id, category_id, year, month, limit_amount) VALUES (?, ?, ?, ?, ?)",
            (user_id, category_id, year, month, limit_amount)
        )
        conn.commit()
        budget_id = cursor.lastrowid
        return MonthlyBudget(id=budget_id, category_id=category_id, 
                            year=year, month=month, limit_amount=limit_amount)

    def list_all(self, user_id: int) -> List[MonthlyBudget]:
        """List all budgets for a user."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, category_id, year, month, limit_amount FROM monthly_budgets WHERE user_id = ?",
            (user_id,)
        )
        return [MonthlyBudget(id=row[0], category_id=row[2], 
                            year=row[3], month=row[4], limit_amount=row[5]) 
                for row in cursor.fetchall()]

    def get_by_id(self, user_id: int, budget_id: int) -> Optional[MonthlyBudget]:
        """Get a specific budget."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, category_id, year, month, limit_amount FROM monthly_budgets WHERE id = ? AND user_id = ?",
            (budget_id, user_id)
        )
        row = cursor.fetchone()
        return MonthlyBudget(id=row[0], category_id=row[2], 
                            year=row[3], month=row[4], limit_amount=row[5]) if row else None

    def update(self, user_id: int, budget_id: int, limit_amount: float) -> None:
        """Update a budget's limit amount."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE monthly_budgets SET limit_amount = ? WHERE id = ? AND user_id = ?",
            (limit_amount, budget_id, user_id)
        )
        conn.commit()

    def delete(self, user_id: int, budget_id: int) -> None:
        """Delete a budget."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM monthly_budgets WHERE id = ? AND user_id = ?",
            (budget_id, user_id)
        )
        conn.commit()
