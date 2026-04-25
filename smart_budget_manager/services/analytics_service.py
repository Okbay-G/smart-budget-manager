"""Analytics and financial calculations service layer.

This module provides all financial calculations and analytics used throughout
the application. Calculations are separate from the data storage and UI layers
to maintain clean separation of concerns.

Classes:
    AnalyticsService: Financial analytics and reporting service.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..domain.models import TxType
from ..domain.repositories import BudgetRepository, CategoryRepository, TransactionRepository


class AnalyticsService:
    """Service for financial analytics and reporting calculations.

    Provides summary statistics, year-to-date trends, and category-based
    breakdowns for financial reporting and visualization.

    Attributes:
        _tx_repo (TransactionRepository): Transaction repository for data access.
        _budget_repo (BudgetRepository): Budget repository for limit data.
        _category_repo (CategoryRepository): Category repository for category lookups.
    """

    def __init__(
        self,
        tx_repo: TransactionRepository,
        budget_repo: BudgetRepository,
        category_repo: CategoryRepository,
    ) -> None:
        """Initialize analytics service with data repositories.

        Args:
            tx_repo (TransactionRepository): Transaction data access.
            budget_repo (BudgetRepository): Budget limit data access.
            category_repo (CategoryRepository): Category data access.
        """
        self._tx_repo = tx_repo
        self._budget_repo = budget_repo
        self._category_repo = category_repo

    def summary(self, user_id: int, year: int, month: int) -> Dict[str, float]:
        """Calculate financial summary for a user for specific month.

        Computes both current month and year-to-date metrics including
        income, expenses, savings, and averages.

        Args:
            user_id (int): ID of user.
            year (int): Year for summary.
            month (int): Month for summary (1-12).

        Returns:
            Dict[str, float]: Summary metrics with keys:
                - 'expenses_month': Current month expenses.
                - 'income_month': Current month income.
                - 'ytd_expenses': Year-to-date total expenses.
                - 'ytd_income': Year-to-date total income.
                - 'ytd_savings': Year-to-date savings (income - expenses).
                - 'monthly_average': Average monthly expenses so far.
                - 'monthly_budget': Sum of all monthly budget limits.
        """
        txs_month = self._tx_repo.list_for_month(user_id, year, month)
        txs_ytd = self._tx_repo.list_for_ytd(user_id, year, month)

        expenses_month = sum(t.amount for t in txs_month if t.tx_type == TxType.EXPENSE)
        income_month = sum(t.amount for t in txs_month if t.tx_type == TxType.INCOME)

        ytd_expenses = sum(t.amount for t in txs_ytd if t.tx_type == TxType.EXPENSE)
        ytd_income = sum(t.amount for t in txs_ytd if t.tx_type == TxType.INCOME)
        ytd_savings = ytd_income - ytd_expenses

        monthly_avg = ytd_expenses / max(1, month)
        monthly_budget = sum(b.limit_amount for b in self._budget_repo.list_for_month(user_id, year, month))

        return {
            "expenses_month": round(expenses_month, 2),
            "income_month": round(income_month, 2),
            "ytd_expenses": round(ytd_expenses, 2),
            "ytd_income": round(ytd_income, 2),
            "ytd_savings": round(ytd_savings, 2),
            "monthly_average": round(monthly_avg, 2),
            "monthly_budget": round(monthly_budget, 2),
        }

    def ytd_series(self, user_id: int, year: int, month: int) -> Dict[str, List[float]]:
        """Generate year-to-date series data for a user for charting.

        Provides month-by-month breakdown of income, expenses, and savings
        from January through the specified month, useful for trend analysis.

        Args:
            user_id (int): ID of user.
            year (int): Year for series.
            month (int): Month to include through (1-12).

        Returns:
            Dict[str, List[float]]: Series data with keys:
                - 'months': List of month numbers (1 to month).
                - 'income': Monthly income values.
                - 'expenses': Monthly expense values.
                - 'savings': Monthly savings values (income - expenses).
        """
        expenses: List[float] = []
        income: List[float] = []
        savings: List[float] = []
        months: List[int] = list(range(1, month + 1))

        for m in months:
            s = self.summary(user_id, year, m)
            expenses.append(s["expenses_month"])
            income.append(s["income_month"])
            savings.append(round(s["income_month"] - s["expenses_month"], 2))

        return {"months": months, "expenses": expenses, "income": income, "savings": savings}

    def expenses_by_category(self, user_id: int, year: int, month: int) -> List[Tuple[str, float]]:
        """Calculate expenses grouped and sorted by category for a user.

        Provides a breakdown of current month expenses by category,
        sorted in descending order by amount spent.

        Args:
            user_id (int): ID of user.
            year (int): Year for breakdown.
            month (int): Month for breakdown (1-12).

        Returns:
            List[Tuple[str, float]]: List of (category_name, amount) tuples
                sorted by amount in descending order.
        """
        txs_month = [t for t in self._tx_repo.list_for_month(user_id, year, month) if t.tx_type == TxType.EXPENSE]

        by_cat: Dict[int, float] = {}
        for t in txs_month:
            if t.category_id is None:
                continue
            by_cat[t.category_id] = by_cat.get(t.category_id, 0.0) + t.amount

        id_to_name = {c.id: c.name for c in self._category_repo.list_all(user_id)}
        items = [(id_to_name.get(cid, f"Category {cid}"), round(total, 2)) for cid, total in by_cat.items()]
        items.sort(key=lambda x: x[1], reverse=True)
        return items
