"""Business logic service layer for budget management.

This module provides the main application service that coordinates between
the presentation layer (UI) and the data layer (repositories). It implements
the service facade pattern to provide a clean, stable API for the UI.

Classes:
    BudgetService: Main application service for budget and transaction management.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace as _replace
from datetime import date
from typing import Dict, List, Optional, Tuple

from .analytics_service import AnalyticsService
from ..domain.exceptions import DuplicateResourceError, RepositoryError
from ..domain.models import Account, Category, MonthlyBudget, Transaction, TxType
from ..domain.repositories import (
    AccountRepository,
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from ..domain.transaction_entities import TransactionFactory
from ..data_access.repositories import (
    SqliteAccountRepository,
    SqliteCategoryRepository,
    SqliteTransactionRepository,
    SqliteBudgetRepository,
)
from ..data_access.db import Db


class BudgetService:
    """Main application service providing UI-facing API for budget management.

    Acts as a facade between the presentation layer and data layer, coordinating
    SQLite repositories and business logic. Provides stable API with persistent
    storage so data survives application restarts.

    Internally uses:
    - SQLite Repositories: Persistent CRUD operations for accounts, categories, budgets, transactions
    - AnalyticsService: Summary calculations and reporting
    - TransactionFactory: Strong OOP validation for transactions

    Attributes:
        _db (Db): Database manager instance.
        _accounts (SqliteAccountRepository): Account repository with SQLite persistence.
        _categories (SqliteCategoryRepository): Category repository with SQLite persistence.
        _budgets (SqliteBudgetRepository): Budget repository with SQLite persistence.
        _transactions (SqliteTransactionRepository): Transaction repository with SQLite persistence.
        _analytics (AnalyticsService): Analytics calculations service.
    """

    def __init__(self, db: Db) -> None:
        """Initialize service with persistent SQLite storage.

        Args:
            db (Db): Database manager instance for accessing SQLite.

        Sets up all repositories pointing to the same database instance.
        Data persists across application restarts.
        """
        self._db = db

        self._accounts = SqliteAccountRepository(db)
        self._categories = SqliteCategoryRepository(db)
        self._budgets = SqliteBudgetRepository(db)
        self._transactions = SqliteTransactionRepository(db)

        self._analytics = AnalyticsService(self._transactions, self._budgets, self._categories)

    # ---------- Dashboard / Analytics API ----------

    def list_months_available(self, user_id: int) -> List[Tuple[int, int]]:
        """Get all months that have transaction data for a user."""
        months = {(t.tx_date.year, t.tx_date.month) for t in self._transactions.list_all(user_id)}
        return sorted(months)

    def get_summary(self, user_id: int, year: int, month: int) -> Dict[str, float]:
        """Get financial summary for a user for specific month."""
        return self._analytics.summary(user_id, year, month)

    def ytd_series(self, user_id: int, year: int, month: int) -> Dict[str, List[float]]:
        """Get year-to-date financial series for a user for charts."""
        return self._analytics.ytd_series(user_id, year, month)

    def expenses_by_category(self, user_id: int, year: int, month: int) -> List[Tuple[str, float]]:
        """Get expenses breakdown by category for a user."""
        return self._analytics.expenses_by_category(user_id, year, month)

    # ---------- Read lists for UI ----------

    def list_transactions(self, user_id: int, year: int, month: int) -> List[Transaction]:
        """Get all transactions for a user for specific month."""
        return self._transactions.list_for_month(user_id, year, month)

    def list_categories(self, user_id: int) -> List[Category]:
        """Get all expense categories for a user."""
        return self._categories.list_all(user_id)

    def list_accounts(self, user_id: int) -> List[Account]:
        """Get all storage accounts for a user."""
        return self._accounts.list_all(user_id)

    def list_budgets(self, user_id: int, year: int, month: int) -> List[MonthlyBudget]:
        """Get all budgets for a user for specific month."""
        return self._budgets.list_for_month(user_id, year, month)

    # ---------- Categories ----------

    def add_category(self, user_id: int, name: str) -> Category:
        """Create new expense category for a user."""
        return self._categories.add(user_id, name)

    def rename_category(self, user_id: int, category_id: int, new_name: str) -> None:
        """Rename existing category for a user."""
        self._categories.rename(user_id, category_id, new_name)

    def delete_category(self, user_id: int, category_id: int) -> None:
        """Delete category for a user (cascades to budgets, nullifies transactions)."""
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM monthly_budgets WHERE category_id = ? AND user_id = ?",
            (category_id, user_id),
        )
        cursor.execute(
            "UPDATE transactions SET category_id = NULL WHERE category_id = ? AND user_id = ?",
            (category_id, user_id),
        )
        cursor.execute(
            "DELETE FROM categories WHERE id = ? AND user_id = ?",
            (category_id, user_id),
        )
        conn.commit()

    # ---------- Accounts ----------

    def add_account(self, user_id: int, name: str) -> Account:
        """Create new account for a user.

        Raises:
            DuplicateResourceError: If account name already exists for this user.
        """
        try:
            return self._accounts.add(user_id, name)
        except sqlite3.IntegrityError:
            raise DuplicateResourceError(f'Account "{name.strip()}" already exists')

    # ---------- Budgets ----------

    def add_budget(self, user_id: int, category_id: int, year: int, month: int, limit_amount: float) -> MonthlyBudget:
        """Create new budget for a user or update if exists."""
        existing = self._budgets.find_for_category_month(user_id, category_id, year, month)
        if existing is not None:
            self._budgets.update(user_id, existing.id, limit_amount)
            return _replace(existing, limit_amount=limit_amount)
        return self._budgets.add(user_id, category_id, year, month, limit_amount)

    def update_budget(self, user_id: int, budget_id: int, *, limit_amount: float) -> None:
        """Update existing budget limit for a user."""
        self._budgets.update(user_id, budget_id, limit_amount)

    def delete_budget(self, user_id: int, budget_id: int) -> None:
        """Delete budget for a user."""
        self._budgets.delete(user_id, budget_id)

    def get_budget_for_category(self, user_id: int, category_id: int, year: int, month: int) -> Optional[MonthlyBudget]:
        """Get budget for a user for a specific category in a month."""
        return self._budgets.find_for_category_month(user_id, category_id, year, month)

    def get_category_spending(self, user_id: int, category_id: int, year: int, month: int) -> float:
        """Get total expenses for a user for a category in a month."""
        transactions = self._transactions.list_for_month(user_id, year, month)
        return sum(
            t.amount for t in transactions
            if t.tx_type == TxType.EXPENSE and t.category_id == category_id
        )

    def can_add_expense(self, user_id: int, category_id: int, amount: float, year: int, month: int) -> Tuple[bool, str]:
        """Check if a user can add an expense without exceeding budget."""
        budget = self.get_budget_for_category(user_id, category_id, year, month)
        if budget is None:
            return False, "Please set a budget for this category first"
        current_spending = self.get_category_spending(user_id, category_id, year, month)
        new_total = current_spending + amount
        if new_total > budget.limit_amount:
            remaining = budget.limit_amount - current_spending
            return False, f"Budget limit exceeded. Remaining budget: CHF {remaining:.2f}"
        return True, ""

    # ---------- Expenses ----------

    def add_expense(
        self,
        user_id: int,
        *,
        account_id: int,
        category_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> Transaction:
        """Add expense for a user.

        Raises:
            RepositoryError: If the transaction cannot be persisted.
        """
        entity = TransactionFactory.create_expense(
            id=0,
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        try:
            return self._transactions.add(user_id, entity.to_dto())
        except sqlite3.IntegrityError as exc:
            raise RepositoryError(f"Failed to persist expense: {exc}") from exc

    def update_expense(
        self,
        user_id: int,
        expense_id: int,
        *,
        account_id: int,
        category_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> None:
        """Update expense for a user."""
        entity = TransactionFactory.create_expense(
            id=expense_id,
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        self._transactions.replace_transaction(user_id, int(expense_id), entity.to_dto())

    def delete_expense(self, user_id: int, expense_id: int) -> None:
        """Delete expense for a user."""
        self._transactions.delete(user_id, int(expense_id))

    # ---------- Income ----------

    def add_income(
        self,
        user_id: int,
        *,
        account_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> Transaction:
        """Add income for a user.

        Raises:
            RepositoryError: If the transaction cannot be persisted.
        """
        entity = TransactionFactory.create_income(
            id=0,
            account_id=account_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        try:
            return self._transactions.add(user_id, entity.to_dto())
        except sqlite3.IntegrityError as exc:
            raise RepositoryError(f"Failed to persist income: {exc}") from exc

    def update_income(
        self,
        user_id: int,
        income_id: int,
        *,
        account_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> None:
        """Update income for a user."""
        entity = TransactionFactory.create_income(
            id=income_id,
            account_id=account_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        self._transactions.replace_transaction(user_id, int(income_id), entity.to_dto())

    def delete_income(self, user_id: int, income_id: int) -> None:
        """Delete income for a user."""
        self._transactions.delete(user_id, int(income_id))
