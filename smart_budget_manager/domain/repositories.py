"""Domain-layer repository interface layer.

This module provides the service layer with a clean interface to persistence
repositories. It abstracts away storage implementation details (SQLite vs in-memory)
from the business logic layer.

Classes:
    BaseRepository: Abstract base for all repositories.
    AccountRepository: Account CRUD operations.
    CategoryRepository: Category CRUD operations.
    BudgetRepository: Budget CRUD operations.
    TransactionRepository: Transaction CRUD operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Generic, Iterable, List, Optional, TypeVar

from .models import Account, Category, MonthlyBudget, Transaction
from .store import InMemoryStore

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common helper methods.

    Provides common functionality for repository implementations including
    ID generation and storage abstraction.

    Attributes:
        _store (InMemoryStore): In-memory data storage.
    """

    def __init__(self, store: InMemoryStore) -> None:
        """Initialize repository with data store.

        Args:
            store (InMemoryStore): Data storage instance.
        """
        self._store = store

    @abstractmethod
    def _items(self) -> List[T]:
        """Get list of items from store.

        Returns:
            List[T]: Items of the repository type.
        """
        raise NotImplementedError

    def _next_id(self, existing_ids: Iterable[int]) -> int:
        """Calculate next available ID for new items.

        Args:
            existing_ids: Iterable of existing ID values.

        Returns:
            int: Next available ID (max + 1, or 1 if empty).
        """
        ids = list(existing_ids)
        return (max(ids) + 1) if ids else 1


class AccountRepository(BaseRepository[Account]):
    """Repository for managing accounts in persistent storage.

    Handles CRUD operations for bank and cash accounts used to categorize
    where money is stored.
    """

    def _items(self) -> List[Account]:
        """Get accounts list.

        Returns:
            List[Account]: All accounts.
        """
        return self._store.accounts

    def list_all(self) -> List[Account]:
        """Retrieve all accounts.

        Returns:
            List[Account]: Copy of all accounts list.
        """
        return list(self._store.accounts)


class CategoryRepository(BaseRepository[Category]):
    """Repository for managing expense categories in persistent storage.

    Handles CRUD operations for expense categories (rent, food, transport, etc.).
    """

    def _items(self) -> List[Category]:
        """Get categories list.

        Returns:
            List[Category]: All categories.
        """
        return self._store.categories

    def list_all(self) -> List[Category]:
        """Retrieve all categories.

        Returns:
            List[Category]: Copy of all categories list.
        """
        return list(self._store.categories)

    def add(self, name: str) -> Category:
        """Create new category.

        Args:
            name (str): Category name (e.g., "Rent", "Food").

        Returns:
            Category: Created category with assigned ID.
        """
        new_id = self._next_id(c.id for c in self._store.categories)
        cat = Category(id=new_id, name=name.strip())
        self._store.categories.append(cat)
        return cat

    def rename(self, category_id: int, new_name: str) -> None:
        """Rename existing category.

        Args:
            category_id (int): ID of category to rename.
            new_name (str): New category name.
        """
        self._store.categories = [
            replace(c, name=new_name.strip()) if c.id == category_id else c
            for c in self._store.categories
        ]

    def delete(self, category_id: int) -> None:
        """Delete category by ID.

        Args:
            category_id (int): ID of category to delete.
        """
        self._store.categories = [c for c in self._store.categories if c.id != category_id]


class BudgetRepository(BaseRepository[MonthlyBudget]):
    """Repository for managing monthly budgets in persistent storage.

    Handles CRUD operations for monthly spending limits per category.
    """

    def _items(self) -> List[MonthlyBudget]:
        """Get budgets list.

        Returns:
            List[MonthlyBudget]: All budgets.
        """
        return self._store.budgets

    def list_for_month(self, year: int, month: int) -> List[MonthlyBudget]:
        """Retrieve budgets for specific month.

        Args:
            year (int): Year to filter by.
            month (int): Month to filter by (1-12).

        Returns:
            List[MonthlyBudget]: Budgets for the specified month.
        """
        return [b for b in self._store.budgets if b.year == year and b.month == month]

    def find_for_category_month(self, category_id: int, year: int, month: int) -> Optional[MonthlyBudget]:
        """Find budget for specific category and month.

        Args:
            category_id (int): Category ID.
            year (int): Year.
            month (int): Month (1-12).

        Returns:
            Optional[MonthlyBudget]: Budget if found, None otherwise.
        """
        return next(
            (b for b in self._store.budgets if b.category_id == category_id and b.year == year and b.month == month),
            None,
        )

    def add(self, category_id: int, year: int, month: int, limit_amount: float) -> MonthlyBudget:
        """Create new budget.

        Args:
            category_id (int): Category ID.
            year (int): Year.
            month (int): Month (1-12).
            limit_amount (float): Spending limit amount.

        Returns:
            MonthlyBudget: Created budget with assigned ID.
        """
        new_id = self._next_id(b.id for b in self._store.budgets)
        b = MonthlyBudget(
            id=new_id,
            category_id=int(category_id),
            year=int(year),
            month=int(month),
            limit_amount=float(limit_amount),
        )
        self._store.budgets.append(b)
        return b

    def update(self, budget_id: int, limit_amount: float) -> None:
        """Update existing budget limit amount.

        Args:
            budget_id (int): ID of budget to update.
            limit_amount (float): New spending limit.
        """
        self._store.budgets = [
            replace(b, limit_amount=float(limit_amount)) if b.id == budget_id else b
            for b in self._store.budgets
        ]

    def delete(self, budget_id: int) -> None:
        """Delete budget by ID.

        Args:
            budget_id (int): ID of budget to delete.
        """
        self._store.budgets = [b for b in self._store.budgets if b.id != budget_id]


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for managing transactions in persistent storage.

    Handles CRUD operations for income and expense transactions.
    """

    def _items(self) -> List[Transaction]:
        """Get transactions list.

        Returns:
            List[Transaction]: All transactions.
        """
        return self._store.transactions

    def list_for_month(self, year: int, month: int) -> List[Transaction]:
        """Retrieve transactions for specific month.

        Args:
            year (int): Year to filter by.
            month (int): Month to filter by (1-12).

        Returns:
            List[Transaction]: Transactions in the specified month.
        """
        return [t for t in self._store.transactions if t.tx_date.year == year and t.tx_date.month == month]

    def list_for_ytd(self, year: int, month: int) -> List[Transaction]:
        """Retrieve transactions from start of year through specified month (YTD).

        Args:
            year (int): Year to filter by.
            month (int): Month to include through (1-12).

        Returns:
            List[Transaction]: Year-to-date transactions.
        """
        return [t for t in self._store.transactions if t.tx_date.year == year and t.tx_date.month <= month]

    def next_id(self) -> int:
        """Get next available transaction ID.

        Returns:
            int: Next ID to use for new transaction.
        """
        return self._next_id(t.id for t in self._store.transactions)

    def add(self, tx: Transaction) -> Transaction:
        """Create new transaction.

        Args:
            tx (Transaction): Transaction to persist.

        Returns:
            Transaction: Persisted transaction (with assigned ID if needed).
        """
        self._store.transactions.append(tx)
        return tx

    def replace_transaction(self, tx_id: int, new_tx: Transaction) -> None:
        """Replace transaction by ID (update operation).

        Args:
            tx_id (int): ID of transaction to replace.
            new_tx (Transaction): New transaction data.
        """
        self._store.transactions = [new_tx if t.id == tx_id else t for t in self._store.transactions]

    def delete(self, tx_id: int) -> None:
        """Delete transaction by ID.

        Args:
            tx_id (int): ID of transaction to delete.
        """
        self._store.transactions = [t for t in self._store.transactions if t.id != tx_id]