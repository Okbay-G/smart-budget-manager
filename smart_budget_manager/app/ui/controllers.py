"""Page controller classes for UI event coordination.

Controllers handle the business-logic coordination between UI pages and services,
translating user actions into service calls and returning structured results.
Pages remain responsible for layout, rendering, and UI state updates.

Following the View → Controller → Service → Repository → DB chain
described in the N-Tier architecture reference.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from ...services.budget_service import BudgetService
from ...domain.exceptions import DuplicateResourceError
from ...domain.models import Account


class ExpenseController:
    """Controller for expense transaction actions."""

    def __init__(self, service: BudgetService) -> None:
        self._svc = service

    def add(
        self,
        user_id: int,
        account_id: int,
        category_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> Tuple[bool, str]:
        """Validate budget, then persist a new expense.

        Returns:
            (True, "Expense added") on success, or (False, reason) on failure.
        """
        ok, reason = self._svc.can_add_expense(user_id, category_id, amount, tx_date.year, tx_date.month)
        if not ok:
            return False, reason
        self._svc.add_expense(
            user_id,
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        return True, "Expense added"

    def update(
        self,
        user_id: int,
        tx_id: int,
        account_id: int,
        category_id: int,
        amount: float,
        description: str,
        tx_date: date,
        old_amount: float,
    ) -> Tuple[bool, str]:
        """Validate budget for the amount delta, then update the expense.

        Returns:
            (True, "Expense updated") on success, or (False, reason) on failure.
        """
        amount_diff = amount - old_amount
        if amount_diff > 0:
            ok, reason = self._svc.can_add_expense(
                user_id, category_id, amount_diff, tx_date.year, tx_date.month
            )
            if not ok:
                return False, reason
        self._svc.update_expense(
            user_id,
            tx_id,
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        return True, "Expense updated"

    def delete(self, user_id: int, tx_id: int) -> Tuple[bool, str]:
        """Delete an expense transaction."""
        self._svc.delete_expense(user_id, tx_id)
        return True, "Expense deleted"


class IncomeController:
    """Controller for income transaction actions."""

    def __init__(self, service: BudgetService) -> None:
        self._svc = service

    def add(
        self,
        user_id: int,
        account_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> Tuple[bool, str]:
        """Persist a new income transaction."""
        self._svc.add_income(
            user_id,
            account_id=account_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        return True, "Income added"

    def update(
        self,
        user_id: int,
        tx_id: int,
        account_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> Tuple[bool, str]:
        """Update an existing income transaction."""
        self._svc.update_income(
            user_id,
            tx_id,
            account_id=account_id,
            amount=amount,
            description=description,
            tx_date=tx_date,
        )
        return True, "Income updated"

    def delete(self, user_id: int, tx_id: int) -> Tuple[bool, str]:
        """Delete an income transaction."""
        self._svc.delete_income(user_id, tx_id)
        return True, "Income deleted"

    def add_account(
        self, user_id: int, name: str
    ) -> Tuple[bool, str, Optional[Account]]:
        """Create a new account, handling duplicate names gracefully.

        Returns:
            (True, message, Account) on success, or (False, message, None) if duplicate.
        """
        try:
            acc = self._svc.add_account(user_id, name)
            return True, f'Account "{acc.name}" created', acc
        except DuplicateResourceError as e:
            return False, str(e), None


class BudgetController:
    """Controller for budget management actions."""

    def __init__(self, service: BudgetService) -> None:
        self._svc = service

    def save(
        self, user_id: int, category_id: int, year: int, month: int, limit: float
    ) -> Tuple[bool, str]:
        """Create or overwrite a monthly budget limit."""
        self._svc.add_budget(user_id, category_id, year, month, limit)
        return True, "Budget saved"

    def update(self, user_id: int, budget_id: int, limit: float) -> Tuple[bool, str]:
        """Update an existing budget limit."""
        self._svc.update_budget(user_id, budget_id, limit_amount=limit)
        return True, "Budget updated"

    def delete(self, user_id: int, budget_id: int) -> Tuple[bool, str]:
        """Delete a monthly budget entry."""
        self._svc.delete_budget(user_id, budget_id)
        return True, "Budget deleted"


class CategoryController:
    """Controller for category management actions."""

    def __init__(self, service: BudgetService) -> None:
        self._svc = service

    def add(self, user_id: int, name: str) -> Tuple[bool, str]:
        """Create a new expense category."""
        self._svc.add_category(user_id, name)
        return True, "Category added"

    def rename(self, user_id: int, category_id: int, new_name: str) -> Tuple[bool, str]:
        """Rename an existing category."""
        self._svc.rename_category(user_id, category_id, new_name)
        return True, "Category renamed"

    def delete(self, user_id: int, category_id: int) -> Tuple[bool, str]:
        """Delete a category (cascades to budgets, nullifies transactions)."""
        self._svc.delete_category(user_id, category_id)
        return True, "Category deleted"
