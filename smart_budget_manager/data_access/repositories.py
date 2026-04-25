"""SQLite-based repository layer for data persistence.

This module implements repository patterns for SQLite data access, providing
CRUD operations for accounts, categories, transactions, and budgets.

Classes:
    SqliteAccountRepository: Repository for account persistence.
    SqliteCategoryRepository: Repository for category persistence.
    SqliteTransactionRepository: Repository for transaction persistence.
    SqliteBudgetRepository: Repository for budget persistence.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, Iterable, List, Optional, TypeVar

from ..domain.models import Account, Category, MonthlyBudget, Transaction, TxType
from .db import Db

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common helper methods.

    Provides foundation for all repository classes with ID generation
    and shared database connection handling.

    Attributes:
        db (Db): Database connection manager.
    """

    def __init__(self, db: Db) -> None:
        """Initialize repository with database connection.

        Args:
            db (Db): Database manager instance.
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

    Provides CRUD operations for bank and cash accounts with user isolation.
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

        Raises:
            sqlite3.IntegrityError: If account name already exists for user.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM accounts WHERE user_id = ? AND LOWER(name) = LOWER(?)",
            (user_id, name.strip())
        )
        if cursor.fetchone():
            raise sqlite3.IntegrityError("UNIQUE constraint failed: accounts.user_id, accounts.name")
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

        Raises:
            sqlite3.IntegrityError: If new name already exists for user.
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


class SqliteCategoryRepository(BaseRepository[Category]):
    """Repository for managing category persistence in SQLite.

    Provides CRUD operations for expense categories with user isolation.
    """

    def list_all(self, user_id: int) -> List[Category]:
        """Retrieve all categories for a user.

        Args:
            user_id (int): ID of user to filter by.

        Returns:
            List[Category]: List of user's categories ordered by name.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories WHERE user_id = ? ORDER BY name", (user_id,))
        return [Category(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def add(self, user_id: int, name: str) -> Category:
        """Create new category for a user.

        Args:
            user_id (int): ID of user creating the category.
            name (str): Category name (e.g., "Rent", "Food").

        Returns:
            Category: Created category with assigned ID.

        Raises:
            sqlite3.IntegrityError: If category name already exists for user.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", (user_id, name.strip()))
        conn.commit()
        return Category(id=cursor.lastrowid, name=name.strip())

    def get_by_id(self, user_id: int, category_id: int) -> Optional[Category]:
        """Get a specific category.

        Args:
            user_id (int): ID of user (for verification).
            category_id (int): ID of category to retrieve.

        Returns:
            Optional[Category]: Category if found, None otherwise.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM categories WHERE id = ? AND user_id = ?",
            (category_id, user_id)
        )
        row = cursor.fetchone()
        return Category(id=row[0], name=row[1]) if row else None

    def rename(self, user_id: int, category_id: int, new_name: str) -> None:
        """Rename existing category for a user.

        Args:
            user_id (int): ID of user (for verification).
            category_id (int): ID of category to rename.
            new_name (str): New category name.

        Raises:
            sqlite3.IntegrityError: If new name already exists for user.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET name = ? WHERE id = ? AND user_id = ?",
            (new_name.strip(), category_id, user_id)
        )
        conn.commit()

    def delete(self, user_id: int, category_id: int) -> None:
        """Delete category for a user.

        Args:
            user_id (int): ID of user (for verification).
            category_id (int): ID of category to delete.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
        conn.commit()


class SqliteTransactionRepository(BaseRepository[Transaction]):
    """Repository for managing transaction persistence in SQLite.

    Provides CRUD operations for income and expense transactions with user isolation.
    """

    def list_all(self, user_id: int) -> List[Transaction]:
        """Retrieve all transactions for a user.

        Args:
            user_id (int): ID of user to filter by.

        Returns:
            List[Transaction]: User's transactions ordered by date descending.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tx_type, account_id, category_id, amount, description, tx_date "
            "FROM transactions WHERE user_id = ? ORDER BY tx_date DESC",
            (user_id,)
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def list_for_month(self, user_id: int, year: int, month: int) -> List[Transaction]:
        """Retrieve transactions for a user in specific month.

        Args:
            user_id (int): ID of user to filter by.
            year (int): Year to filter by.
            month (int): Month to filter by (1-12).

        Returns:
            List[Transaction]: User's transactions in the specified month.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tx_type, account_id, category_id, amount, description, tx_date "
            "FROM transactions "
            "WHERE user_id = ? "
            "AND CAST(strftime('%Y', tx_date) AS INTEGER) = ? "
            "AND CAST(strftime('%m', tx_date) AS INTEGER) = ? "
            "ORDER BY tx_date DESC",
            (user_id, year, month),
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def list_for_ytd(self, user_id: int, year: int, month: int) -> List[Transaction]:
        """Retrieve user's transactions from start of year through specified month (YTD).

        Args:
            user_id (int): ID of user to filter by.
            year (int): Year to filter by.
            month (int): Month to include through (1-12).

        Returns:
            List[Transaction]: User's year-to-date transactions.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tx_type, account_id, category_id, amount, description, tx_date "
            "FROM transactions "
            "WHERE user_id = ? "
            "AND CAST(strftime('%Y', tx_date) AS INTEGER) = ? "
            "AND CAST(strftime('%m', tx_date) AS INTEGER) <= ? "
            "ORDER BY tx_date",
            (user_id, year, month),
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def next_id(self) -> int:
        """Get next available transaction ID.

        Returns:
            int: Next ID to use for new transaction.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM transactions")
        result = cursor.fetchone()
        return (result[0] + 1) if result[0] is not None else 1

    def add(self, user_id: int, tx: Transaction) -> Transaction:
        """Create new transaction for a user.

        Args:
            user_id (int): ID of user creating the transaction.
            tx (Transaction): Transaction to persist.

        Returns:
            Transaction: Transaction with assigned ID from database.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (user_id, tx_type, account_id, category_id, amount, description, tx_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, tx.tx_type.value, tx.account_id, tx.category_id, tx.amount, tx.description, tx.tx_date),
        )
        conn.commit()
        return Transaction(
            id=cursor.lastrowid,
            tx_type=tx.tx_type,
            account_id=tx.account_id,
            category_id=tx.category_id,
            amount=tx.amount,
            description=tx.description,
            tx_date=tx.tx_date,
        )

    def replace_transaction(self, user_id: int, tx_id: int, new_tx: Transaction) -> None:
        """Replace transaction by ID (update) for a user.

        Args:
            user_id (int): ID of user (for verification).
            tx_id (int): ID of transaction to replace.
            new_tx (Transaction): New transaction data.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transactions SET tx_type = ?, account_id = ?, category_id = ?, "
            "amount = ?, description = ?, tx_date = ? WHERE id = ? AND user_id = ?",
            (new_tx.tx_type.value, new_tx.account_id, new_tx.category_id, new_tx.amount, new_tx.description, new_tx.tx_date, tx_id, user_id),
        )
        conn.commit()

    def delete(self, user_id: int, tx_id: int) -> None:
        """Delete transaction for a user.

        Args:
            user_id (int): ID of user (for verification).
            tx_id (int): ID of transaction to delete.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
        conn.commit()

    def delete_by_category(self, user_id: int, category_id: int) -> None:
        """Delete all transactions for a category for a user.

        Args:
            user_id (int): ID of user (for verification).
            category_id (int): Category ID whose transactions to delete.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE category_id = ? AND user_id = ?", (category_id, user_id))
        conn.commit()

    def clear_category_reference(self, user_id: int, category_id: int) -> None:
        """Clear category reference from user's transactions (set to NULL).

        Used when deleting category to keep transaction history.

        Args:
            user_id (int): ID of user (for verification).
            category_id (int): Category ID to clear from transactions.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET category_id = NULL WHERE category_id = ? AND user_id = ?", (category_id, user_id))
        conn.commit()

    @staticmethod
    def _row_to_transaction(row: tuple) -> Transaction:
        """Convert database row to Transaction object.

        Args:
            row: Database row tuple.

        Returns:
            Transaction: Converted transaction object.
        """
        return Transaction(
            id=row[0],
            tx_type=TxType(row[1]),
            account_id=row[2],
            category_id=row[3],
            amount=row[4],
            description=row[5],
            tx_date=datetime.strptime(row[6], "%Y-%m-%d").date(),
        )


class SqliteBudgetRepository(BaseRepository[MonthlyBudget]):
    """Repository for managing monthly budget persistence in SQLite.

    Provides CRUD operations for monthly spending limits per category with user isolation.
    """

    def list_all(self, user_id: int) -> List[MonthlyBudget]:
        """Retrieve all budgets for a user.

        Args:
            user_id (int): ID of user to filter by.

        Returns:
            List[MonthlyBudget]: User's budgets ordered by year/month.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, category_id, year, month, limit_amount FROM monthly_budgets "
            "WHERE user_id = ? ORDER BY year, month",
            (user_id,)
        )
        return [MonthlyBudget(id=row[0], category_id=row[1], year=row[2], month=row[3], limit_amount=row[4]) for row in cursor.fetchall()]

    def list_for_month(self, user_id: int, year: int, month: int) -> List[MonthlyBudget]:
        """Retrieve budgets for a user for specific month.

        Args:
            user_id (int): ID of user to filter by.
            year (int): Year to filter by.
            month (int): Month to filter by (1-12).

        Returns:
            List[MonthlyBudget]: User's budgets for the specified month.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, category_id, year, month, limit_amount FROM monthly_budgets "
            "WHERE user_id = ? AND year = ? AND month = ? ORDER BY category_id",
            (user_id, year, month),
        )
        return [MonthlyBudget(id=row[0], category_id=row[1], year=row[2], month=row[3], limit_amount=row[4]) for row in cursor.fetchall()]

    def find_for_category_month(self, user_id: int, category_id: int, year: int, month: int) -> Optional[MonthlyBudget]:
        """Find budget for a user for specific category and month.

        Args:
            user_id (int): ID of user to filter by.
            category_id (int): Category ID.
            year (int): Year.
            month (int): Month (1-12).

        Returns:
            Optional[MonthlyBudget]: Budget if found, None otherwise.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, category_id, year, month, limit_amount FROM monthly_budgets "
            "WHERE user_id = ? AND category_id = ? AND year = ? AND month = ?",
            (user_id, category_id, year, month),
        )
        row = cursor.fetchone()
        if row:
            return MonthlyBudget(id=row[0], category_id=row[1], year=row[2], month=row[3], limit_amount=row[4])
        return None

    def get_by_id(self, user_id: int, budget_id: int) -> Optional[MonthlyBudget]:
        """Get a specific budget.

        Args:
            user_id (int): ID of user (for verification).
            budget_id (int): ID of budget to retrieve.

        Returns:
            Optional[MonthlyBudget]: Budget if found, None otherwise.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, category_id, year, month, limit_amount FROM monthly_budgets WHERE id = ? AND user_id = ?",
            (budget_id, user_id),
        )
        row = cursor.fetchone()
        if row:
            return MonthlyBudget(id=row[0], category_id=row[1], year=row[2], month=row[3], limit_amount=row[4])
        return None

    def add(self, user_id: int, category_id: int, year: int, month: int, limit_amount: float) -> MonthlyBudget:
        """Create new budget for a user.

        Args:
            user_id (int): ID of user creating the budget.
            category_id (int): Category ID.
            year (int): Year.
            month (int): Month (1-12).
            limit_amount (float): Spending limit amount.

        Returns:
            MonthlyBudget: Created budget with assigned ID.

        Raises:
            sqlite3.IntegrityError: If budget already exists for this user/category/month.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO monthly_budgets (user_id, category_id, year, month, limit_amount) VALUES (?, ?, ?, ?, ?)",
            (user_id, category_id, year, month, limit_amount),
        )
        conn.commit()
        return MonthlyBudget(id=cursor.lastrowid, category_id=category_id, year=year, month=month, limit_amount=limit_amount)

    def update(self, user_id: int, budget_id: int, limit_amount: float) -> None:
        """Update budget limit amount for a user.

        Args:
            user_id (int): ID of user (for verification).
            budget_id (int): ID of budget to update.
            limit_amount (float): New spending limit.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE monthly_budgets SET limit_amount = ? WHERE id = ? AND user_id = ?",
            (limit_amount, budget_id, user_id),
        )
        conn.commit()

    def delete(self, user_id: int, budget_id: int) -> None:
        """Delete budget for a user.

        Args:
            user_id (int): ID of user (for verification).
            budget_id (int): ID of budget to delete.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM monthly_budgets WHERE id = ? AND user_id = ?", (budget_id, user_id))
        conn.commit()
