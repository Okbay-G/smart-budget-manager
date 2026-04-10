"""Domain models for budget management.

This module defines the core data models used throughout the application.
All models are implemented as frozen dataclasses (immutable) to ensure
data integrity and thread-safety.

Classes:
    TxType: Transaction type enumeration (INCOME or EXPENSE).
    Category: Expense category model.
    Account: Storage account model.
    Transaction: Transaction (income or expense) model.
    MonthlyBudget: Monthly spending limit per category model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class TxType(str, Enum):
    """Transaction type enumeration.

    Attributes:
        INCOME: Income transaction type.
        EXPENSE: Expense transaction type.
    """
    INCOME = "income"
    EXPENSE = "expense"


@dataclass(frozen=True)
class Category:
    """Expense category model.

    Represents a category for categorizing expenses (e.g., Rent, Food, Transport).

    Attributes:
        id (int): Unique category identifier.
        name (str): Category name (e.g., "Rent", "Food").
    """
    id: int
    name: str

    def __str__(self) -> str:
        """Return category name.
        
        Returns:
            str: Category name.
        """
        return self.name

    def __repr__(self) -> str:
        """Return detailed category representation.
        
        Returns:
            str: Detailed object representation.
        """
        return f"Category(id={self.id}, name='{self.name}')"

    def __lt__(self, other: Category) -> bool:
        """Compare categories by name for sorting.
        
        Args:
            other: Another Category object.
            
        Returns:
            bool: True if this category name comes before other.
        """
        if not isinstance(other, Category):
            return NotImplemented
        return self.name < other.name


@dataclass(frozen=True)
class Account:
    """Storage account model.

    Represents a financial account or storage location for money (e.g., Bank, Cash).

    Attributes:
        id (int): Unique account identifier.
        name (str): Account name (e.g., "Bank", "Cash").
    """
    id: int
    name: str

    def __str__(self) -> str:
        """Return account name.
        
        Returns:
            str: Account name.
        """
        return self.name

    def __repr__(self) -> str:
        """Return detailed account representation.
        
        Returns:
            str: Detailed object representation.
        """
        return f"Account(id={self.id}, name='{self.name}')"

    def __lt__(self, other: Account) -> bool:
        """Compare accounts by name for sorting.
        
        Args:
            other: Another Account object.
            
        Returns:
            bool: True if this account name comes before other.
        """
        if not isinstance(other, Account):
            return NotImplemented
        return self.name < other.name


@dataclass(frozen=True)
class Transaction:
    """Transaction model for income and expense records.

    Represents a single income or expense transaction with associated metadata.

    Attributes:
        id (int): Unique transaction identifier.
        tx_type (TxType): Transaction type (INCOME or EXPENSE).
        account_id (int): ID of account where transaction occurred.
        category_id (Optional[int]): ID of category (expenses only; None for income).
        amount (float): Transaction amount (always positive).
        description (str): Transaction description/notes.
        tx_date (date): Date when transaction occurred.
    """
    id: int
    tx_type: TxType
    account_id: int
    category_id: Optional[int]  # income may not need a category
    amount: float
    description: str
    tx_date: date

    def __str__(self) -> str:
        """Return transaction summary.
        
        Returns:
            str: Summary of transaction (type, amount, description).
        """
        return f"{self.tx_type.value.upper()} {self.amount} - {self.description}"

    def __repr__(self) -> str:
        """Return detailed transaction representation.
        
        Returns:
            str: Detailed object representation.
        """
        return (f"Transaction(id={self.id}, tx_type={self.tx_type}, "
                f"account_id={self.account_id}, category_id={self.category_id}, "
                f"amount={self.amount}, description='{self.description}', "
                f"tx_date={self.tx_date})")

    def __lt__(self, other: Transaction) -> bool:
        """Compare transactions by date (most recent first).
        
        Args:
            other: Another Transaction object.
            
        Returns:
            bool: True if this transaction date is after other (reversed for recent first).
        """
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.tx_date > other.tx_date


@dataclass(frozen=True)
class MonthlyBudget:
    """Monthly budget limit model.

    Represents a monthly spending cap for a particular expense category.

    Attributes:
        id (int): Unique budget identifier.
        category_id (int): Category this budget applies to.
        year (int): Budget year.
        month (int): Budget month (1-12).
        limit_amount (float): Monthly spending limit in currency units.
    """
    id: int
    category_id: int
    year: int
    month: int
    limit_amount: float

    def __str__(self) -> str:
        """Return budget summary.
        
        Returns:
            str: Summary (category_id, year, month, limit).
        """
        return f"Budget {self.year}-{self.month:02d}: ${self.limit_amount}"

    def __repr__(self) -> str:
        """Return detailed budget representation.
        
        Returns:
            str: Detailed object representation.
        """
        return (f"MonthlyBudget(id={self.id}, category_id={self.category_id}, "
                f"year={self.year}, month={self.month}, limit_amount={self.limit_amount})")

    def __lt__(self, other: MonthlyBudget) -> bool:
        """Compare budgets by month/year.
        
        Args:
            other: Another MonthlyBudget object.
            
        Returns:
            bool: True if this budget is earlier in time.
        """
        if not isinstance(other, MonthlyBudget):
            return NotImplemented
        if self.year != other.year:
            return self.year < other.year
        return self.month < other.month
