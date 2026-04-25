"""Business logic service layer for budget management.

"""

from __future__ import annotations

from datetime import date
from typing import Any

from ..persistence.db import Db
from ..persistence.repositories import (
    SqliteAccountRepository,
    SqliteCategoryRepository,
    SqliteTransactionRepository,
    SqliteBudgetRepository,
)
from .models import Account, Category, MonthlyBudget, Transaction, TxType


class BudgetService:
    """Main application service providing UI-facing API for budget management."""

    def __init__(self, db: Db) -> None:
        self._db = db
        self._accounts = SqliteAccountRepository(db)
        self._categories = SqliteCategoryRepository(db)
        self._budgets = SqliteBudgetRepository(db)
        self._transactions = SqliteTransactionRepository(db)

    # ------------------------------------------------------------------ accounts
    def list_accounts(self, user_id: int) -> list[Account]:
        return self._accounts.list_all(user_id)

    def add_account(self, user_id: int, name: str) -> Account:
        return self._accounts.add(user_id, name)

    # ------------------------------------------------------------------ categories
    def list_categories(self, user_id: int) -> list[Category]:
        return self._categories.list_all(user_id)

    def add_category(self, user_id: int, name: str) -> Category:
        return self._categories.add(user_id, name)

    def rename_category(self, user_id: int, category_id: int, new_name: str) -> None:
        self._categories.rename(user_id, category_id, new_name)

    def delete_category(self, user_id: int, category_id: int) -> None:
        # Perform all three SQL operations atomically in one transaction
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

    # ------------------------------------------------------------------ transactions
    def list_transactions(self, user_id: int, year: int, month: int) -> list[Transaction]:
        return self._transactions.list_for_month(user_id, year, month)

    def list_months_available(self, user_id: int) -> list[tuple[int, int]]:
        """Return distinct (year, month) tuples for which the user has transactions."""
        conn = self._db.get_connection()
        rows = conn.execute(
            "SELECT DISTINCT "
            "CAST(strftime('%Y', tx_date) AS INTEGER) AS y, "
            "CAST(strftime('%m', tx_date) AS INTEGER) AS m "
            "FROM transactions WHERE user_id = ? ORDER BY y, m",
            (user_id,),
        ).fetchall()
        return [(int(r[0]), int(r[1])) for r in rows]

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
        tx = Transaction(
            id=0, tx_type=TxType.EXPENSE, account_id=account_id,
            category_id=category_id, amount=amount, description=description, tx_date=tx_date,
        )
        return self._transactions.add(user_id, tx)

    def update_expense(
        self,
        user_id: int,
        tx_id: int,
        *,
        account_id: int,
        category_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> None:
        tx = Transaction(
            id=tx_id, tx_type=TxType.EXPENSE, account_id=account_id,
            category_id=category_id, amount=amount, description=description, tx_date=tx_date,
        )
        self._transactions.replace_transaction(user_id, tx_id, tx)

    def delete_expense(self, user_id: int, tx_id: int) -> None:
        self._transactions.delete(user_id, tx_id)

    def add_income(
        self,
        user_id: int,
        *,
        account_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> Transaction:
        tx = Transaction(
            id=0, tx_type=TxType.INCOME, account_id=account_id,
            category_id=None, amount=amount, description=description, tx_date=tx_date,
        )
        return self._transactions.add(user_id, tx)

    def update_income(
        self,
        user_id: int,
        tx_id: int,
        *,
        account_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> None:
        tx = Transaction(
            id=tx_id, tx_type=TxType.INCOME, account_id=account_id,
            category_id=None, amount=amount, description=description, tx_date=tx_date,
        )
        self._transactions.replace_transaction(user_id, tx_id, tx)

    def delete_income(self, user_id: int, tx_id: int) -> None:
        self._transactions.delete(user_id, tx_id)

    # ------------------------------------------------------------------ budgets
    def list_budgets(self, user_id: int, year: int, month: int) -> list[MonthlyBudget]:
        return [
            b for b in self._budgets.list_all(user_id)
            if b.year == year and b.month == month
        ]

    def add_budget(
        self, user_id: int, category_id: int, year: int, month: int, limit_amount: float
    ) -> MonthlyBudget:
        return self._budgets.add(user_id, category_id, year, month, limit_amount)

    def update_budget(
        self,
        user_id: int,
        budget_id: int,
        *,
        limit_amount: float,
    ) -> None:
        self._budgets.update(user_id, budget_id, limit_amount)

    def delete_budget(self, user_id: int, budget_id: int) -> None:
        self._budgets.delete(user_id, budget_id)

    def can_add_expense(
        self, user_id: int, category_id: int, amount: float, year: int, month: int
    ) -> tuple[bool, str]:
        """Check whether adding `amount` to this category would exceed its monthly budget."""
        budgets = [
            b for b in self._budgets.list_all(user_id)
            if b.category_id == category_id and b.year == year and b.month == month
        ]
        if not budgets:
            return False, "Please set a budget for this category first."
        budget = budgets[0]
        spent = sum(
            t.amount for t in self._transactions.list_for_month(user_id, year, month)
            if t.tx_type == TxType.EXPENSE and t.category_id == category_id
        )
        if spent + amount > budget.limit_amount:
            return False, (
                f"Budget exceeded: CHF {spent + amount:,.2f} would exceed "
                f"the CHF {budget.limit_amount:,.2f} limit."
            )
        return True, ""

    # ------------------------------------------------------------------ analytics
    def get_summary(self, user_id: int, year: int, month: int) -> dict[str, float]:
        """Return KPI summary dict for the dashboard."""
        ytd_txs = self._transactions.list_for_ytd(user_id, year, month)
        ytd_income = sum(t.amount for t in ytd_txs if t.tx_type == TxType.INCOME)
        ytd_expenses = sum(t.amount for t in ytd_txs if t.tx_type == TxType.EXPENSE)
        ytd_savings = ytd_income - ytd_expenses
        months_elapsed = month  # Jan–month
        monthly_average = ytd_expenses / months_elapsed if months_elapsed else 0.0
        monthly_budget = sum(
            b.limit_amount for b in self._budgets.list_all(user_id)
            if b.year == year and b.month == month
        )
        return {
            "ytd_expenses": ytd_expenses,
            "ytd_savings": ytd_savings,
            "monthly_average": monthly_average,
            "monthly_budget": monthly_budget,
        }

    def ytd_series(self, user_id: int, year: int, month: int) -> dict[str, Any]:
        """Return per-month income/expense/savings series for YTD line chart."""
        months = list(range(1, month + 1))
        income_series: list[float] = []
        expense_series: list[float] = []
        savings_series: list[float] = []
        for m in months:
            txs = self._transactions.list_for_month(user_id, year, m)
            inc = sum(t.amount for t in txs if t.tx_type == TxType.INCOME)
            exp = sum(t.amount for t in txs if t.tx_type == TxType.EXPENSE)
            income_series.append(round(inc, 2))
            expense_series.append(round(exp, 2))
            savings_series.append(round(inc - exp, 2))
        return {"months": months, "income": income_series, "expenses": expense_series, "savings": savings_series}

    def expenses_by_category(self, user_id: int, year: int, month: int) -> list[tuple[str, float]]:
        """Return list of (category_name, total_amount) for expense donut chart."""
        txs = self._transactions.list_for_month(user_id, year, month)
        cats = {c.id: c.name for c in self._categories.list_all(user_id)}
        totals: dict[str, float] = {}
        for t in txs:
            if t.tx_type != TxType.EXPENSE:
                continue
            name = cats.get(t.category_id, "Uncategorised")
            totals[name] = totals.get(name, 0.0) + float(t.amount)
        return sorted(totals.items(), key=lambda x: x[1], reverse=True)

