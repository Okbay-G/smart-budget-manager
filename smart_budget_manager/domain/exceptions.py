"""Custom exception classes for domain layer violations and errors.

This module defines custom exceptions used throughout the application domain,
following the Single Responsibility Principle.

Exceptions:
    DomainError: Base exception for domain-related errors.
    AuthenticationError: Authentication and authorization related errors.
    ValidationError: Data validation errors.
    ResourceNotFoundError: Resource not found errors.
    DuplicateResourceError: Duplicate resource creation attempted.
    RepositoryError: Repository operation errors.
"""


class DomainError(Exception):
    """Base exception for all domain-layer errors.
    
    Serves as the root exception class for all domain-specific errors,
    allowing for catching all domain errors with a single except clause.
    """
    pass


class AuthenticationError(DomainError):
    """Exception raised for authentication failures.
    
    Raised when:
    - User login fails (invalid credentials)
    - User registration fails (email conflicts, invalid data)
    - Session management errors occur
    
    Inherits from DomainError for consistent error handling.
    """
    pass


class ValidationError(DomainError):
    """Exception raised for data validation failures.
    
    Raised when:
    - Transaction validation fails (negative amounts, missing fields)
    - Budget data is invalid (invalid month values, negative limits)
    - Category or account data violates constraints
    
    Inherits from DomainError for consistent error handling.
    """
    pass


class ResourceNotFoundError(DomainError):
    """Exception raised when a requested resource is not found.
    
    Raised when:
    - Transaction with ID does not exist
    - Category cannot be found
    - User is not found
    - Budget does not exist
    
    Inherits from DomainError for consistent error handling.
    """
    pass


class DuplicateResourceError(DomainError):
    """Exception raised when attempting to create a duplicate resource.
    
    Raised when:
    - Email already registered (during user registration)
    - Category name already exists for user
    - Account name already exists for user
    
    Inherits from DomainError for consistent error handling.
    """
    pass


class RepositoryError(DomainError):
    """Exception raised for repository operation failures.
    
    Raised when:
    - Database operations fail (SQLite errors)
    - Data consistency violations occur
    - Transaction operations cannot be completed
    
    Inherits from DomainError for consistent error handling.
    """
    pass
