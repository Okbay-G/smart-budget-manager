"""Strong OOP domain entities for transaction management with validation.

This module implements domain-driven design patterns for transaction management,
providing type-specific subclasses (Expense vs Income) and validation via a factory.
All entities are immutable (frozen dataclasses) to ensure consistency.

Classes:
    ExpenseTransaction: Expense-specific transaction implementation.
    IncomeTransaction: Income-specific transaction implementation.
    TransactionFactory: Factory for creating and validating transaction instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from .exceptions import ValidationError
from .models import Transaction, TxType


@dataclass(frozen=True)
class TransactionEntity(ABC):
    """Abstract base class for strongly-typed transaction entities.

    Provides a polymorphic, type-safe way to handle income and expense
    transactions with different validation rules. Subclasses enforce
    type-specific business rules.

    Attributes:
        id (int): Unique transaction identifier.
        account_id (int): ID of account where transaction occurred.
        amount (float): Transaction amount (always positive).
        description (str): Transaction description/notes.
        tx_date (date): Date when transaction occurred.
    """
    
    id: int
    account_id: int
    amount: float
    description: str
    tx_date: date

    @property
    @abstractmethod
    def tx_type(self) -> TxType:
        """Get transaction type (INCOME or EXPENSE).
        
        Returns:
            TxType: Type of transaction.
        """
        raise NotImplementedError

    @abstractmethod
    def category_id(self) -> int | None:
        """Get category ID (type-specific).
        
        Returns:
            int | None: Category ID for expenses, None for income.
        """
        raise NotImplementedError

    def validate_common(self) -> None:
        """Validate common transaction rules.

        Checks that apply to both income and expenses:
        - Account is valid (> 0)
        - Amount is positive
        - Description is not empty
        - Date is a valid date

        Raises:
            ValidationError: If any common rule is violated.
        """
        if self.account_id <= 0:
            raise ValidationError("Account must be selected.")
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than 0.")
        if not self.description or not self.description.strip():
            raise ValidationError("Description must not be empty.")
        if not isinstance(self.tx_date, date):
            raise ValidationError("Transaction date must be a date.")

    @abstractmethod
    def validate(self) -> None:
        """Perform complete validation including type-specific rules.

        Must be called before converting to DTO for persistence.

        Raises:
            ValidationError: If any rule is violated.
        """
        raise NotImplementedError

    def to_dto(self) -> Transaction:
        """Convert to transaction DTO for persistence.

        Transforms this domain entity into the data transfer object
        used by repositories and the UI layer.

        Returns:
            Transaction: DTO representation of this transaction.
        """
        return Transaction(
            id=self.id,
            tx_type=self.tx_type,
            account_id=self.account_id,
            category_id=self.category_id(),
            amount=float(self.amount),
            description=self.description.strip(),
            tx_date=self.tx_date,
        )

    def __str__(self) -> str:
        """Return transaction summary.
        
        Returns:
            str: Summary of transaction entity.
        """
        return f"{self.tx_type.value.upper()} {self.amount} - {self.description}"

    def __repr__(self) -> str:
        """Return detailed transaction entity representation.
        
        Returns:
            str: Detailed object representation.
        """
        return (f"{self.__class__.__name__}(id={self.id}, "
                f"account_id={self.account_id}, amount={self.amount}, "
                f"description='{self.description}', tx_date={self.tx_date})")


@dataclass(frozen=True)
class ExpenseTransaction(TransactionEntity):
    """Expense transaction entity with expense-specific validation.

    Expenses require a valid category assignment. Encodes the business
    rule that expenses must be categorized for reporting and budgeting.

    Attributes:
        _category_id (int): Category ID for this expense (private, use property).
    """
    
    _category_id: int

    @property
    def tx_type(self) -> TxType:
        """Get transaction type.

        Returns:
            TxType: TxType.EXPENSE
        """
        return TxType.EXPENSE

    def category_id(self) -> int | None:
        """Get expense category ID.

        Returns:
            int: Category ID for this expense.
        """
        return int(self._category_id)

    def validate(self) -> None:
        """Validate expense-specific rules.

        Ensures that expense has a valid category assigned.

        Raises:
            ValidationError: If category is missing or invalid.
        """
        self.validate_common()
        if self._category_id is None or int(self._category_id) <= 0:
            raise ValidationError("Expense must have a category.")

    def __repr__(self) -> str:
        """Return detailed expense transaction representation.
        
        Returns:
            str: Detailed object representation.
        """
        return (f"ExpenseTransaction(id={self.id}, account_id={self.account_id}, "
                f"category_id={self._category_id}, amount={self.amount}, "
                f"description='{self.description}', tx_date={self.tx_date})")


@dataclass(frozen=True)
class IncomeTransaction(TransactionEntity):
    """Income transaction entity with income-specific validation.

    Income transactions do not require a category, as categorization
    is only needed for expense analysis and budgeting.
    """

    @property
    def tx_type(self) -> TxType:
        """Get transaction type.

        Returns:
            TxType: TxType.INCOME
        """
        return TxType.INCOME

    def category_id(self) -> int | None:
        """Income has no category.

        Returns:
            None: Income transactions are not categorized.
        """
        return None

    def validate(self) -> None:
        """Validate income-specific rules.

        Income has no type-specific validation beyond common rules
        (amount > 0, valid account, etc.).
        """
        self.validate_common()

    def __repr__(self) -> str:
        """Return detailed income transaction representation.
        
        Returns:
            str: Detailed object representation.
        """
        return (f"IncomeTransaction(id={self.id}, account_id={self.account_id}, "
                f"amount={self.amount}, description='{self.description}', "
                f"tx_date={self.tx_date})")


class TransactionFactory:
    """Factory for creating validated transaction entities.

    Provides static methods to construct transaction objects with
    automatic validation according to domain rules. Ensures all
    transactions created through this factory are valid.
    """

    @staticmethod
    def create_expense(
        *,
        id: int,
        account_id: int,
        category_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> ExpenseTransaction:
        """Create a validated expense transaction.

        Args:
            id (int): Transaction ID.
            account_id (int): Account where expense occurred.
            category_id (int): Category for the expense.
            amount (float): Expense amount (must be > 0).
            description (str): Expense description.
            tx_date (date): Date of expense.

        Returns:
            ExpenseTransaction: Validated expense entity.

        Raises:
            ValidationError: If any business rule is violated.
        """
        tx = ExpenseTransaction(
            id=int(id),
            account_id=int(account_id),
            _category_id=int(category_id),
            amount=float(amount),
            description=str(description),
            tx_date=tx_date,
        )
        tx.validate()
        return tx

    @staticmethod
    def create_income(
        *,
        id: int,
        account_id: int,
        amount: float,
        description: str,
        tx_date: date,
    ) -> IncomeTransaction:
        """Create a validated income transaction.

        Args:
            id (int): Transaction ID.
            account_id (int): Account where income was deposited.
            amount (float): Income amount (must be > 0).
            description (str): Income description.
            tx_date (date): Date of income.

        Returns:
            IncomeTransaction: Validated income entity.

        Raises:
            ValidationError: If any business rule is violated.
        """
        tx = IncomeTransaction(
            id=int(id),
            account_id=int(account_id),
            amount=float(amount),
            description=str(description),
            tx_date=tx_date,
        )
        tx.validate()
        return tx
