"""Database initialization and connection management layer.

This module handles SQLite database setup, connection management, and schema initialization.
It provides a clean interface for database operations while keeping SQL access isolated
from the rest of the application.

Classes:
    Db: Manages SQLite database connection and initialization.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class Db:
    """SQLite database connection and schema manager.

    Manages SQLite database initialization, connection, and schema creation.
    Provides a singleton-like connection interface for the application.

    Attributes:
        db_path (str): Path to the SQLite database file.
        _connection (Optional[sqlite3.Connection]): Active database connection.

    Example:
        db = Db("budget.db")
        db.initialize()
        conn = db.get_connection()
    """

    def __init__(self, db_path: str = "budget.db") -> None:
        """Initialize database manager.

        Args:
            db_path (str): Path to SQLite database file. Defaults to "budget.db".
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def initialize(self) -> None:
        """Initialize database connection and create schema if needed.

        Creates necessary tables (accounts, categories, transactions, budgets)
        with proper relationships and constraints. Safe to call multiple times.
        """
        self.connect()
        self._create_schema()

    def connect(self) -> None:
        """Establish SQLite database connection.

        Opens a connection to the database file and enables foreign keys.
        If called when already connected, reuses existing connection.
        """
        if self._connection is None:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.db_path)
            self._connection.execute("PRAGMA foreign_keys = ON")

    def get_connection(self) -> sqlite3.Connection:
        """Get active database connection.

        Returns:
            sqlite3.Connection: Active database connection.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if self._connection is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _create_schema(self) -> None:
        """Create database schema if it doesn't exist.

        Creates the following tables:
        - users: User accounts with email as unique identifier
        - accounts: Storage accounts (bank, cash, etc.)
        - categories: Expense categories (rent, food, etc.)
        - transactions: Income/expense transactions
        - monthly_budgets: Monthly spending limits per category
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            username TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, name)
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, name)
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tx_type TEXT NOT NULL CHECK(tx_type IN ('income', 'expense')),
            account_id INTEGER NOT NULL,
            category_id INTEGER,
            amount REAL NOT NULL CHECK(amount > 0),
            description TEXT NOT NULL,
            tx_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE RESTRICT,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS monthly_budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
            limit_amount REAL NOT NULL CHECK(limit_amount > 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE(user_id, category_id, year, month)
        )""")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(tx_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_month ON monthly_budgets(year, month)")

        conn.commit()
