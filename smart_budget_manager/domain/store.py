"""Data store abstraction layer.

This module defines the data storage interface and provides implementations
for both in-memory and SQLite-based persistence. The Service layer uses this
abstraction to remain agnostic of the underlying storage mechanism.

Classes:
    InMemoryStore: In-memory data storage (for testing/demo).
    SQLiteStore: SQLite-based persistent data storage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from .models import Account, Category, MonthlyBudget, Transaction


@dataclass
class InMemoryStore:
    """In-memory data store for demo and testing purposes.

    Acts like a tiny in-memory database. Useful for development and testing,
    but data is lost when the application stops.

    Attributes:
        accounts (List[Account]): All bank/cash accounts.
        categories (List[Category]): All expense categories.
        budgets (List[MonthlyBudget]): All monthly budgets.
        transactions (List[Transaction]): All income/expense transactions.

    Note:
        Later you can replace this with SQLite repositories without changing the UI.
    """

    accounts: List[Account] = field(default_factory=list)
    categories: List[Category] = field(default_factory=list)
    budgets: List[MonthlyBudget] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)