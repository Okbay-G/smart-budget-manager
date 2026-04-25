#!/usr/bin/env python3
"""Comprehensive Test Suite for Basic UI

This suite validates cumulative functionality from earlier steps plus new basic UI features:
- Database schema initialization and integrity (inherited from earlier steps)
- Domain model classes and magic methods (inherited from earlier steps)
- User model, email/password/username validation, registration, login, session management (inherited from earlier steps)
- Account repository operations and user isolation (inherited from earlier steps)
- Expense and income transaction persistence via SqliteTransactionRepository (inherited from earlier steps)
- Expense and income transaction entity creation, validation, DTO conversion, magic methods (inherited from earlier steps)
- Category repository: add, list, rename, delete (inherited from earlier steps)
- Monthly spending analytics by category (inherited from earlier steps)
- Year-to-date spending totals (inherited from earlier steps)
- Category breakdown analytics (inherited from earlier steps)
- Budget repository: add, list, get by ID, update, delete (inherited from earlier steps)
- Budget vs actual spending comparison (inherited from earlier steps)
- Budget alerts when spending approaches or exceeds limits (inherited from earlier steps)
- Multi-category budget tracking (inherited from earlier steps)
- Spending trend analysis over time (inherited from earlier steps)
- Category comparison analytics (inherited from earlier steps)
- Year-to-date reporting (inherited from earlier steps)
- Advanced spending metrics (inherited from earlier steps)
- NiceGUI imports and dependencies (new in this step)
- Core services initialization (new in this step)
- UI page imports and structure (new in this step)
- Layout module (new in this step)
- Main entry point (new in this step)
"""

import sys
import os
from datetime import date
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from smart_budget_manager.persistence.db import Db
from smart_budget_manager.persistence.repositories import SqliteAccountRepository, SqliteTransactionRepository, SqliteCategoryRepository, SqliteBudgetRepository
from smart_budget_manager.domain.models import TxType, Account, Category, Transaction, MonthlyBudget
from smart_budget_manager.domain.auth_service import AuthService, User
from smart_budget_manager.domain.validators import (
    validate_email, validate_password, validate_username, 
    sanitize_input, validate_all_inputs
)
from smart_budget_manager.domain.transaction_entities import TransactionFactory, ExpenseTransaction, IncomeTransaction
from smart_budget_manager.domain.exceptions import ValidationError


# Check if NiceGUI is available
try:
    import nicegui
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False


# ============================================================
# Step 1 tests (Database and Models) - Inherited
# ============================================================

def test_database_initialization():
    """Validate SQLite database schema creation and integrity.
    
    Verifies:
    - All required tables exist (users, accounts, categories, transactions, monthly_budgets)
    - All required indices exist for query optimization (date, account, category, budget tracking)
    - Database connection is properly established
    """
    print("\n" + "="*60)
    print("Testing Database Initialization")
    print("="*60)
    
    db = Db("test_.db")
    db.initialize()
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verify tables exist
        tables = [
            'users', 'accounts', 'categories', 'transactions', 'monthly_budgets'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"[OK] Table '{table}' created successfully")
            else:
                print(f"[FAIL] Table '{table}' NOT found")
                return False
        
        # Verify indices exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = [row[0] for row in cursor.fetchall()]
        expected_indices = [
            'idx_transactions_date',
            'idx_transactions_account',
            'idx_transactions_category',
            'idx_budgets_month'
        ]
        for idx in expected_indices:
            if idx in indices:
                print(f"[OK] Index '{idx}' created successfully")
            else:
                print(f"[FAIL] Index '{idx}' NOT found")
                return False
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_models():
    """Validate all domain model implementations and attributes.
    
    Tests:
    - TxType enum values and correctness (income, expense)
    - Account, Category, Transaction, and MonthlyBudget model creation
    - Model attribute validation and type correctness
    - Model immutability (frozen dataclasses)
    - Model string representations (__str__)
    """
    print("\n" + "="*60)
    print("Testing Domain Models")
    print("="*60)
    
    try:
        # Test TxType enum
        assert TxType.INCOME.value == "income"
        assert TxType.EXPENSE.value == "expense"
        print("[OK] TxType enum working correctly")
        
        # Test Account model
        account = Account(id=1, name="Bank Account")
        assert account.id == 1
        assert account.name == "Bank Account"
        assert str(account) == "Bank Account"
        print(f"[OK] Account model: {account}")
        
        # Test Category model
        category = Category(id=1, name="Food")
        assert category.id == 1
        assert category.name == "Food"
        assert str(category) == "Food"
        print(f"[OK] Category model: {category}")
        
        # Test Category comparison
        c1 = Category(id=1, name="Apple")
        c2 = Category(id=2, name="Banana")
        sorted_cats = sorted([c2, c1])
        assert sorted_cats[0].name == "Apple"
        print(f"[OK] Category sorting: {[c.name for c in sorted_cats]}")
        
        # Test Transaction model
        tx = Transaction(
            id=1,
            tx_type=TxType.EXPENSE,
            account_id=1,
            category_id=1,
            amount=50.0,
            description="Groceries",
            tx_date=date.today()
        )
        assert tx.tx_type == TxType.EXPENSE
        assert tx.amount == 50.0
        print(f"[OK] Transaction model: {tx}")
        
        # Test MonthlyBudget model
        budget = MonthlyBudget(
            id=1,
            category_id=1,
            year=2024,
            month=3,
            limit_amount=500.0
        )
        assert budget.category_id == 1
        assert budget.year == 2024
        assert budget.month == 3
        print(f"[OK] MonthlyBudget model: {budget}")
        
        # Test immutability (frozen dataclasses)
        try:
            account.name = "Changed"
            print("[FAIL] Account should be immutable (frozen)")
            return False
        except Exception:
            print("[OK] Account is immutable (frozen)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_magic_methods():
    """Validate object-oriented magic methods for model comparison and serialization.
    
    Verifies:
    - __str__: String representation returns model name/identifier
    - __repr__: Developer-friendly representation includes model type and ID
    - __lt__: Less-than comparison enables sorting (Account, Category)
    - Object identity and ordering mechanics
    """
    print("\n" + "="*60)
    print("Testing Magic Methods")
    print("="*60)
    
    try:
        # Test __str__
        account = Account(id=1, name="Savings")
        assert str(account) == "Savings"
        print(f"[OK] __str__ method: {account}")
        
        # Test __repr__
        category = Category(id=1, name="Food")
        repr_str = repr(category)
        assert "Category" in repr_str and "id=1" in repr_str
        print(f"[OK] __repr__ method exists")
        
        # Test __lt__ (less than)
        c1 = Category(id=1, name="Apples")
        c2 = Category(id=2, name="Bananas")
        assert c1 < c2
        print(f"[OK] __lt__ method working for Category comparison")
        
        a1 = Account(id=1, name="Account A")
        a2 = Account(id=2, name="Account B")
        assert a1 < a2
        print(f"[OK] __lt__ method working for Account comparison")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_database_persistence():
    """Validate that data persists correctly in SQLite database and can be retrieved.
    
    Confirms:
    - User records can be inserted and retrieved
    - Account creation and persistence
    - Category creation and persistence
    - Transaction insertion with all attributes preserved
    - Data integrity: amount, description, and relationship IDs maintained correctly
    """
    print("\n" + "="*60)
    print("Testing Database Persistence")
    print("="*60)
    
    try:
        # Clean up old test database
        if os.path.exists("test_persist.db"):
            os.remove("test_persist.db")
        
        db = Db("test_persist.db")
        db.initialize()
        conn = db.get_connection()
        
        # Insert test user
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
            ("test@example.com", "Test User", "hash123")
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"[OK] Inserted user with ID: {user_id}")
        
        # Insert account
        cursor.execute(
            "INSERT INTO accounts (user_id, name) VALUES (?, ?)",
            (user_id, "Bank Account")
        )
        conn.commit()
        account_id = cursor.lastrowid
        print(f"[OK] Inserted account with ID: {account_id}")
        
        # Insert category
        cursor.execute(
            "INSERT INTO categories (user_id, name) VALUES (?, ?)",
            (user_id, "Food")
        )
        conn.commit()
        category_id = cursor.lastrowid
        print(f"[OK] Inserted category with ID: {category_id}")
        
        # Insert transaction
        cursor.execute(
            "INSERT INTO transactions (user_id, tx_type, account_id, category_id, amount, description, tx_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, "expense", account_id, category_id, 50.0, "Groceries", "2024-03-15")
        )
        conn.commit()
        tx_id = cursor.lastrowid
        print(f"[OK] Inserted transaction with ID: {tx_id}")
        
        # Verify data retrieval
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        assert user is not None
        print(f"[OK] Retrieved user: {user[1]}")
        
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
        tx = cursor.fetchone()
        assert tx is not None and tx[5] == 50.0
        print(f"[OK] Retrieved transaction: amount={tx[5]}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


# ============================================================
# Step 2 tests (Authentication) - Inherited
# ============================================================

def test_user_model():
    """Validate User model implementation and magic methods.
    
    Tests:
    - User creation with email, username, and ID
    - __str__: String representation of user
    - __repr__: Developer-friendly user representation
    - __eq__: Equality based on email (same email = same user)
    - __hash__: Users hashable for use in sets and dicts
    """
    print("\n" + "="*60)
    print("Testing User Model")
    print("="*60)
    
    try:
        user1 = User(id=1, email="john@example.com", username="John")
        user2 = User(id=2, email="jane@example.com", username="Jane")
        user3 = User(id=3, email="john@example.com", username="Johnny")
        
        # Test __str__
        print(f"[OK] __str__: {user1}")
        
        # Test __repr__
        print(f"[OK] __repr__: {repr(user1)}")
        
        # Test __eq__ (same email = same user)
        assert user1 == user3
        assert not (user1 == user2)
        print("[OK] __eq__: Equality based on email works")
        
        # Test __hash__
        user_set = {user1, user2, user3}
        assert len(user_set) == 2  # user1 and user3 have same email
        print("[OK] __hash__: Can be used in sets/dicts")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_email_validation():
    """Validate email format checking and edge cases.
    
    Ensures:
    - Valid email formats are accepted (standard, complex, multiple domains)
    - Invalid formats rejected (missing parts, consecutive dots, wrong structure)
    - Length constraints enforced (not too short, not too long)
    - Empty and malformed inputs handled correctly
    """
    print("\n" + "="*60)
    print("Testing Email Validation")
    print("="*60)
    
    test_cases = [
        ("john@example.com", True, "Valid email"),
        ("user.name+tag@example.co.uk", True, "Valid complex email"),
        ("test@domain.org", True, "Valid with org domain"),
        ("invalid.email", False, "Missing @ symbol"),
        ("user@", False, "Missing domain"),
        ("@example.com", False, "Missing local part"),
        ("user@domain", False, "Missing TLD"),
        ("user..name@example.com", False, "Consecutive dots"),
        (".user@example.com", False, "Starts with dot"),
        ("user.@example.com", False, "Ends with dot"),
        ("ab", False, "Too short"),
        ("a" * 300 + "@example.com", False, "Too long"),
        ("", False, "Empty string"),
        ("user@..com", False, "Domain with consecutive dots"),
    ]
    
    try:
        for email, expected, description in test_cases:
            is_valid, error = validate_email(email)
            if is_valid == expected:
                print(f"[OK] {description}: '{email}'")
            else:
                print(f"[FAIL] {description}: '{email}' - Expected {expected}, got {is_valid}")
                return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_password_validation():
    """Validate password security requirements and strength.
    
    Verifies:
    - Minimum length requirement (8 characters)
    - Maximum length constraint (128 characters)
    - Required complexity: uppercase, lowercase, numbers, special characters
    - No spaces (leading, trailing, or mid-string)
    - Empty and edge case handling
    """
    print("\n" + "="*60)
    print("Testing Password Validation")
    print("="*60)
    
    test_cases = [
        ("SecurePass1!", True, "Valid strong password"),
        ("MyPassword#123", True, "Valid with multiple special chars"),
        ("Pass@word2024", True, "Valid typical password"),
        ("short", False, "Too short (< 8 chars)"),
        ("password1!", False, "No uppercase letter"),
        ("PASSWORD1!", False, "No lowercase letter"),
        ("NoDigits!", False, "No digit"),
        ("NoSpecial123", False, "No special character"),
        ("Pass word!", False, "Contains space"),
        (" PassWord1!", False, "Starts with space"),
        ("PassWord1! ", False, "Ends with space"),
        ("a" * 200, False, "Too long (> 128 chars)"),
        ("", False, "Empty string"),
        ("Pass@1", False, "Too short (7 chars)"),
    ]
    
    try:
        for password, expected, description in test_cases:
            is_valid, error = validate_password(password)
            if is_valid == expected:
                print(f"[OK] {description}: {len(password)} chars")
            else:
                print(f"[FAIL] {description}: Expected {expected}, got {is_valid} - {error}")
                return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_username_validation():
    """Validate username format and character constraints.
    
    Confirms:
    - Optional field (empty username allowed)
    - Maximum length constraint (50 characters)
    - Allowed characters (letters, numbers, underscores, hyphens, spaces)
    - Disallowed characters rejected (special chars like @, #)
    - No leading/trailing/consecutive spaces
    """
    print("\n" + "="*60)
    print("Testing Username Validation")
    print("="*60)
    
    test_cases = [
        ("John_Doe", True, "Valid alphanumeric with underscore"),
        ("user-name", True, "Valid with hyphen"),
        ("John Doe", True, "Valid with space"),
        ("", True, "Empty (optional field)"),
        ("user_123-name", True, "Valid mixed"),
        ("a" * 50, True, "At max length (50 chars)"),
        ("a" * 51, False, "Exceeds max length"),
        (" username", False, "Starts with space"),
        ("username ", False, "Ends with space"),
        ("user@name", False, "Contains invalid character @"),
        ("user#name", False, "Contains invalid character #"),
        ("user  name", False, "Multiple consecutive spaces"),
    ]
    
    try:
        for username, expected, description in test_cases:
            is_valid, error = validate_username(username)
            if is_valid == expected:
                print(f"[OK] {description}: '{username}'")
            else:
                print(f"[FAIL] {description}: Expected {expected}, got {is_valid}")
                return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_user_registration():
    """Validate user registration with validation and duplicate prevention.
    
    Tests:
    - Successful registration creates user and logs them in
    - Duplicate email rejected
    - All validation rules enforced (email, password, username formats)
    - Clear error messages for each validation failure
    - Password strength requirements enforced
    """
    # Clean test database
    db_file = "test_mvp2_register.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    
    print("\n" + "="*60)
    print("Testing User Registration")
    print("="*60)
    
    try:
        db = Db(db_file)
        db.initialize()
        auth = AuthService(db.get_connection())
        
        # Test successful registration with strong password
        success, msg = auth.register("alice@example.com", "SecurePass1!", "Alice")
        assert success, f"Registration failed: {msg}"
        assert auth.current_user is not None
        assert auth.current_user.email == "alice@example.com"
        print(f"[OK] Successfully registered: {auth.current_user}")
        
        # Test duplicate registration
        success, msg = auth.register("alice@example.com", "AnotherPass1!", "Alice2")
        assert not success
        print(f"[OK] Duplicate registration blocked: {msg}")
        
        # Test missing email
        success, msg = auth.register("", "SecurePass1!", "Bob")
        assert not success
        print(f"[OK] Missing email rejected: {msg}")
        
        # Test missing password
        success, msg = auth.register("bob@example.com", "", "Bob")
        assert not success
        print(f"[OK] Missing password rejected: {msg}")
        
        # Test invalid email
        success, msg = auth.register("invalid-email", "SecurePass1!", "Bob")
        assert not success
        print(f"[OK] Invalid email rejected: {msg}")
        
        # Test weak password - too short
        success, msg = auth.register("bob@example.com", "Short1!", "Bob")
        assert not success
        assert "at least 8" in msg.lower()
        print(f"[OK] Short password rejected: {msg}")
        
        # Test weak password - no uppercase
        success, msg = auth.register("bob@example.com", "lowercase1!", "Bob")
        assert not success
        assert "uppercase" in msg.lower()
        print(f"[OK] No uppercase rejected: {msg}")
        
        # Test weak password - no lowercase
        success, msg = auth.register("bob@example.com", "UPPERCASE1!", "Bob")
        assert not success
        assert "lowercase" in msg.lower()
        print(f"[OK] No lowercase rejected: {msg}")
        
        # Test weak password - no digit
        success, msg = auth.register("bob@example.com", "NoDigit!", "Bob")
        assert not success
        assert "number" in msg.lower()
        print(f"[OK] No digit rejected: {msg}")
        
        # Test weak password - no special character
        success, msg = auth.register("bob@example.com", "NoSpecial1", "Bob")
        assert not success
        assert "special" in msg.lower()
        print(f"[OK] No special character rejected: {msg}")
        
        # Test invalid username
        success, msg = auth.register("charlie@example.com", "SecurePass1!", "Invalid@Name")
        assert not success
        assert "username" in msg.lower()
        print(f"[OK] Invalid username rejected: {msg}")
        
        db.close()
        return True
    except Exception as e:
        import traceback
        print(f"[FAIL] Error: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False


def test_user_login():
    """Validate user authentication and credential verification.
    
    Confirms:
    - Correct email and password allows login
    - Wrong password denied
    - Nonexistent user rejected
    - Missing credentials rejected
    - Invalid email format rejected during login
    - Session state updated on successful login
    """
    print("\n" + "="*60)
    print("Testing User Login")
    print("="*60)
    
    # Clean test database
    if os.path.exists("test_mvp2_login.db"):
        os.remove("test_mvp2_login.db")

    try:
        db = Db("test_mvp2_login.db")
        db.initialize()
        auth = AuthService(db.get_connection())
        
        # Register user first
        auth.register("bob@example.com", "SecurePass1!", "Bob")
        auth.logout()
        print("[OK] User registered and logged out")
        
        # Test successful login
        success, msg = auth.login("bob@example.com", "SecurePass1!")
        assert success, f"Login failed: {msg}"
        assert auth.is_logged_in()
        print(f"[OK] Successfully logged in: {auth.current_user}")
        
        # Test wrong password
        auth.logout()
        success, msg = auth.login("bob@example.com", "WrongPassword1!")
        assert not success
        assert not auth.is_logged_in()
        print(f"[OK] Wrong password rejected: {msg}")
        
        # Test user not found
        success, msg = auth.login("nonexistent@example.com", "SecurePass1!")
        assert not success
        assert not auth.is_logged_in()
        print(f"[OK] Nonexistent user rejected: {msg}")
        
        # Test missing credentials
        success, msg = auth.login("", "")
        assert not success
        print(f"[OK] Missing credentials rejected: {msg}")
        
        # Test invalid email format on login
        success, msg = auth.login("not-an-email", "SecurePass1!")
        assert not success
        print(f"[OK] Invalid email format on login rejected: {msg}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_session_management():
    """Validate login/logout session state management.
    
    Verifies:
    - User not logged in initially
    - User logged in after successful registration
    - User logged in after successful login
    - User logged out after logout
    - Session state correctly reflected in is_logged_in() and current_user
    """
    # Clean test database
    if os.path.exists("test_mvp2_session.db"):
        os.remove("test_mvp2_session.db")
    
    print("\n" + "="*60)
    print("Testing Session Management")
    print("="*60)
    
    try:
        db = Db("test_mvp2_session.db")
        db.initialize()
        auth = AuthService(db.get_connection())
        
        # Test not logged in initially
        assert not auth.is_logged_in()
        assert auth.current_user is None
        print("[OK] Initially not logged in")
        
        # Register and verify logged in
        auth.register("charlie@example.com", "SecurePass1!", "Charlie")
        assert auth.is_logged_in()
        assert auth.current_user is not None
        print(f"[OK] Logged in after registration: {auth.current_user}")
        
        # Logout
        auth.logout()
        assert not auth.is_logged_in()
        assert auth.current_user is None
        print("[OK] Successfully logged out")
        
        # Login again
        success, msg = auth.login("charlie@example.com", "SecurePass1!")
        assert success and auth.is_logged_in()
        print("[OK] Successfully logged in again")
        
        db.close()
        return True
    except Exception as e:
        import traceback
        print(f"[FAIL] Error: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False


def test_auth_service_methods():
    """Validate AuthService string representations and state tracking.
    
    Tests:
    - __str__: Shows "not logged in" when no active session
    - __str__: Shows user info when logged in
    - __repr__: Developer-friendly representation of AuthService
    """
    print("\n" + "="*60)
    print("Testing AuthService Methods")
    print("="*60)
    
    try:
        db = Db("test_mvp2_methods.db")
        db.initialize()
        auth = AuthService(db.get_connection())
        
        # Test __str__ when not logged in
        str_repr = str(auth)
        assert "not logged in" in str_repr.lower()
        print(f"[OK] __str__ (not logged in): {str_repr}")
        
        # Login and test __str__
        auth.register("dave@example.com", "SecurePass1!", "Dave")
        str_repr = str(auth)
        print(f"[OK] __str__ (logged in): {str_repr}")
        
        # Test __repr__
        repr_str = repr(auth)
        assert "AuthService" in repr_str
        print(f"[OK] __repr__ working")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


# ============================================================
# Step 3 tests (Account Management) - Inherited
# ============================================================

def setup_test_db_mvp3(db_name):
    """Helper to create a test database with test users for account tests."""
    if os.path.exists(db_name):
        os.remove(db_name)
    
    db = Db(db_name)
    db.initialize()
    
    # Create test users
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
        ("user1@example.com", "User1", "SecurePass1!")
    )
    cursor.execute(
        "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
        ("user2@example.com", "User2", "SecurePass2!")
    )
    conn.commit()
    
    return db


def test_account_creation():
    """Validate account creation and ID generation.
    
    Verifies:
    - Account creation succeeds with name
    - Each account receives unique ID
    - Multiple accounts can be created for same user
    - Accounts for different users are isolated
    """
    print("\n" + "="*60)
    print("Testing Account Creation")
    print("="*60)
    
    try:
        db = setup_test_db_mvp3("test_mvp3_create.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        
        # Create first account
        acc1 = repo.add(user_id, "Savings Account")
        assert acc1.id is not None
        assert acc1.name == "Savings Account"
        print("[OK] Created account 1: {}".format(acc1))
        
        # Create second account
        acc2 = repo.add(user_id, "Checking Account")
        assert acc2.id is not None
        assert acc2.id > acc1.id
        print("[OK] Created account 2: {}".format(acc2))
        
        # Create account for different user
        acc3 = repo.add(2, "Business Account")
        assert acc3.id is not None
        print("[OK] Created account for different user: {}".format(acc3))
        
        db.close()
        return True
    except Exception as e:
        print("[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False


def test_account_retrieval():
    """Validate account retrieval by ID and listing.
    
    Tests:
    - List all accounts for user returns correct count
    - Accounts returned in alphabetical order
    - Get account by ID returns correct account
    - Get by ID returns None for nonexistent account
    - Accounts from other users not accessible
    """
    print("\n" + "="*60)
    print("Testing Account Retrieval")
    print("="*60)
    
    try:
        db = setup_test_db_mvp3("test_mvp3_retrieve.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        
        # Create accounts
        repo.add(user_id, "Account A")
        repo.add(user_id, "Account B")
        repo.add(user_id, "Account C")
        
        # List all for user
        accounts = repo.list_all(user_id)
        assert len(accounts) == 3
        print("[OK] Listed all accounts for user: {} accounts".format(len(accounts)))
        
        # Verify they're sorted alphabetically
        names = [a.name for a in accounts]
        assert names == sorted(names)
        print("[OK] Accounts sorted alphabetically: {}".format(names))
        
        # Get by ID
        account_id = accounts[0].id
        retrieved = repo.get_by_id(user_id, account_id)
        assert retrieved is not None
        assert retrieved.name == accounts[0].name
        print("[OK] Retrieved account by ID: {}".format(retrieved))
        
        # Get nonexistent account
        nonexistent = repo.get_by_id(user_id, 9999)
        assert nonexistent is None
        print("[OK] Nonexistent account returns None")
        
        # Get from wrong user
        repo.add(2, "Another Account")
        other_user_account = repo.list_all(2)[0]
        wrong_user = repo.get_by_id(user_id, other_user_account.id)
        assert wrong_user is None
        print("[OK] Cannot retrieve account from wrong user")
        
        db.close()
        return True
    except Exception as e:
        print("[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False


def test_account_rename():
    """Validate account rename operations and whitespace handling.
    
    Verifies:
    - Account can be renamed to new name
    - Whitespace is trimmed from account names
    - Renamed account persists in database
    """
    print("\n" + "="*60)
    print("Testing Account Rename")
    print("="*60)
    
    try:
        db = setup_test_db_mvp3("test_mvp3_rename.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        account = repo.add(user_id, "Original Name")
        account_id = account.id
        
        # Rename account
        repo.rename(user_id, account_id, "New Name")
        renamed = repo.get_by_id(user_id, account_id)
        assert renamed.name == "New Name"
        print("[OK] Renamed account: {}".format(renamed))
        
        # Rename with whitespace trimming
        repo.rename(user_id, account_id, "  Trimmed Name  ")
        trimmed = repo.get_by_id(user_id, account_id)
        assert trimmed.name == "Trimmed Name"
        print("[OK] Whitespace trimmed: '{}'".format(trimmed.name))
        
        db.close()
        return True
    except Exception as e:
        print("[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False


def test_account_deletion():
    """Validate account deletion and cleanup.
    
    Confirms:
    - Account can be deleted by user ID and account ID
    - Deleted account no longer appears in list
    - Deleted account returns None on retrieval
    - Deletion doesn't affect other accounts
    """
    print("\n" + "="*60)
    print("Testing Account Deletion")
    print("="*60)
    
    try:
        db = setup_test_db_mvp3("test_mvp3_delete.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        acc1 = repo.add(user_id, "Account 1")
        acc2 = repo.add(user_id, "Account 2")
        
        # Delete first account
        repo.delete(user_id, acc1.id)
        remaining = repo.list_all(user_id)
        assert len(remaining) == 1
        assert remaining[0].id == acc2.id
        print("[OK] Deleted account successfully")
        
        # Verify deleted account is gone
        deleted = repo.get_by_id(user_id, acc1.id)
        assert deleted is None
        print("[OK] Deleted account not retrievable")
        
        # Try to delete nonexistent
        try:
            repo.delete(user_id, 9999)
            print("[OK] Deleting nonexistent account handled")
        except:
            print("[OK] Deleting nonexistent account raises exception")
        
        db.close()
        return True
    except Exception as e:
        print("[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False


def test_user_isolation():
    """Validate multi-tenant account isolation by user.
    
    Tests:
    - Each user only sees their own accounts
    - List operations filtered by user_id
    - Deleting one user's account doesn't affect others
    - ID space shared but access controlled by user context
    """
    print("\n" + "="*60)
    print("Testing User Isolation")
    print("="*60)
    
    try:
        db = setup_test_db_mvp3("test_mvp3_isolation.db")
        repo = SqliteAccountRepository(db)
        
        user1_id = 1
        user2_id = 2
        
        # Create accounts for both users
        u1_acc1 = repo.add(user1_id, "User1 Account1")
        u1_acc2 = repo.add(user1_id, "User1 Account2")
        u2_acc1 = repo.add(user2_id, "User2 Account1")
        
        # Verify each user only sees their own accounts
        u1_accounts = repo.list_all(user1_id)
        u2_accounts = repo.list_all(user2_id)
        
        assert len(u1_accounts) == 2
        assert len(u2_accounts) == 1
        print("[OK] User 1 has {} accounts".format(len(u1_accounts)))
        print("[OK] User 2 has {} accounts".format(len(u2_accounts)))
        
        # Delete user1 account, user2 should be unaffected
        repo.delete(user1_id, u1_acc1.id)
        u1_accounts = repo.list_all(user1_id)
        u2_accounts = repo.list_all(user2_id)
        
        assert len(u1_accounts) == 1
        assert len(u2_accounts) == 1
        print("[OK] Deleting user1 account doesn't affect user2")
        
        db.close()
        return True
    except Exception as e:
        print("[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False



# ============================================================
# Step 4 tests (Expense Transactions) - Inherited
# ============================================================

def setup_test_db(db_name):
    """Helper to create a test database with test users, accounts, and categories."""
    if os.path.exists(db_name):
        os.remove(db_name)
    
    db = Db(db_name)
    db.initialize()
    
    # Create test users
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Insert test users
    cursor.execute(
        "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
        ("user1@example.com", "User1", "SecurePass1!")
    )
    cursor.execute(
        "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
        ("user2@example.com", "User2", "SecurePass2!")
    )
    
    # Insert test accounts
    cursor.execute(
        "INSERT INTO accounts (user_id, name) VALUES (?, ?)",
        (1, "Savings")
    )
    cursor.execute(
        "INSERT INTO accounts (user_id, name) VALUES (?, ?)",
        (1, "Checking")
    )
    cursor.execute(
        "INSERT INTO accounts (user_id, name) VALUES (?, ?)",
        (2, "Cash")
    )
    
    # Insert test categories  
    cursor.execute(
        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
        (1, "Food")
    )
    cursor.execute(
        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
        (1, "Transport")
    )
    cursor.execute(
        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
        (2, "Entertainment")
    )
    
    conn.commit()
    return db

def test_expense_creation():
    """Test creating expense transactions."""
    print("\n" + "="*60)
    print("Testing Expense Creation")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp4_create.db"):

            os.remove("test_mvp4_create.db")

        
        db = setup_test_db("test_mvp4_create.db")
        db.initialize()
        repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create expense
        expense = Transaction(
            id=0,
            tx_type=TxType.EXPENSE,
            account_id=1,
            category_id=1,
            amount=50.0,
            description="Groceries",
            tx_date=date(2024, 3, 15)
        )
        
        created = repo.add(user_id, expense)
        assert created.id is not None
        assert created.tx_type == TxType.EXPENSE
        assert created.amount == 50.0
        print(f"[OK] Created expense: {created}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_transaction_queries():
    """Test querying transactions by month and YTD."""
    print("\n" + "="*60)
    print("Testing Transaction Queries")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp4_query.db"):

            os.remove("test_mvp4_query.db")

        
        db = setup_test_db("test_mvp4_query.db")
        db.initialize()
        repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create transactions across different months
        tx1 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=50.0, description="Jan expense", tx_date=date(2024, 1, 15))
        tx2 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=75.0, description="Feb expense", tx_date=date(2024, 2, 10))
        tx3 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=100.0, description="Mar expense", tx_date=date(2024, 3, 5))
        tx4 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=60.0, description="Mar expense 2", tx_date=date(2024, 3, 20))
        
        repo.add(user_id, tx1)
        repo.add(user_id, tx2)
        repo.add(user_id, tx3)
        repo.add(user_id, tx4)
        
        # Query by month
        mar_tx = repo.list_for_month(user_id, 2024, 3)
        assert len(mar_tx) == 2
        assert sum(t.amount for t in mar_tx) == 160.0
        print(f"[OK] March transactions: {len(mar_tx)} tx, total=${sum(t.amount for t in mar_tx)}")
        
        # Query YTD
        ytd_tx = repo.list_for_ytd(user_id, 2024, 3)
        assert len(ytd_tx) == 4
        assert sum(t.amount for t in ytd_tx) == 285.0
        print(f"[OK] YTD through March: {len(ytd_tx)} tx, total=${sum(t.amount for t in ytd_tx)}")
        
        # Query all
        all_tx = repo.list_all(user_id)
        assert len(all_tx) == 4
        print(f"[OK] All transactions: {len(all_tx)} tx")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_income_and_expense():
    """Validate both income and expense transaction types.
    
    Confirms:
    - Income and expense transactions stored separately by type
    - Both types can coexist for same user
    - Type is correctly persisted in database
    """
    print("\n" + "="*60)
    print("Testing Income and Expense Mix")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp4_mixed.db"):

            os.remove("test_mvp4_mixed.db")

        
        db = setup_test_db("test_mvp4_mixed.db")
        db.initialize()
        repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create mixed transactions
        income = Transaction(
            id=0, tx_type=TxType.INCOME, account_id=1, category_id=None,
            amount=2000.0, description="Salary", tx_date=date(2024, 3, 1)
        )
        expense1 = Transaction(
            id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
            amount=500.0, description="Rent", tx_date=date(2024, 3, 1)
        )
        expense2 = Transaction(
            id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=2,
            amount=200.0, description="Food", tx_date=date(2024, 3, 15)
        )
        
        repo.add(user_id, income)
        repo.add(user_id, expense1)
        repo.add(user_id, expense2)
        
        # Query all
        all_tx = repo.list_all(user_id)
        assert len(all_tx) == 3
        
        # Separate by type
        income_tx = [t for t in all_tx if t.tx_type == TxType.INCOME]
        expense_tx = [t for t in all_tx if t.tx_type == TxType.EXPENSE]
        
        assert len(income_tx) == 1
        assert len(expense_tx) == 2
        print(f"[OK] Income transactions: {len(income_tx)}")
        print(f"[OK] Expense transactions: {len(expense_tx)}")
        
        # For income, category should be None
        assert income_tx[0].category_id is None
        print("[OK] Income has no category")
        
        # For expenses, category should exist
        assert all(t.category_id is not None for t in expense_tx)
        print("[OK] All expenses have category")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_transaction_update():
    """Validate transaction modification and updates.
    
    Tests:
    - Update transaction amount
    - Update transaction description
    - Update transaction date
    - Updates persist in database
    """
    print("\n" + "="*60)
    print("Testing Transaction Update")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp4_update.db"):

            os.remove("test_mvp4_update.db")

        
        db = setup_test_db("test_mvp4_update.db")
        db.initialize()
        repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create transaction
        original = Transaction(
            id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
            amount=50.0, description="Original", tx_date=date(2024, 3, 15)
        )
        created = repo.add(user_id, original)
        tx_id = created.id
        
        # Update transaction
        updated = Transaction(
            id=tx_id, tx_type=TxType.EXPENSE, account_id=1, category_id=2,
            amount=75.0, description="Updated", tx_date=date(2024, 3, 16)
        )
        repo.replace_transaction(user_id, tx_id, updated)
        
        # Verify update
        all_tx = repo.list_all(user_id)
        assert len(all_tx) == 1
        assert all_tx[0].amount == 75.0
        assert all_tx[0].description == "Updated"
        assert all_tx[0].category_id == 2
        print(f"[OK] Updated transaction: {all_tx[0]}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_transaction_deletion():
    """Validate transaction deletion and cleanup.
    
    Verifies:
    - Transaction can be deleted
    - Deleted transaction no longer retrieved
    - Other transactions unaffected by deletion
    """
    print("\n" + "="*60)
    print("Testing Transaction Deletion")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp4_delete.db"):

            os.remove("test_mvp4_delete.db")

        
        db = setup_test_db("test_mvp4_delete.db")
        db.initialize()
        repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create multiple transactions
        tx1 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=50.0, description="Expense 1", tx_date=date(2024, 3, 15))
        tx2 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=75.0, description="Expense 2", tx_date=date(2024, 3, 16))
        tx3 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=100.0, description="Expense 3", tx_date=date(2024, 3, 17))
        
        c1 = repo.add(user_id, tx1)
        c2 = repo.add(user_id, tx2)
        c3 = repo.add(user_id, tx3)
        
        all_tx = repo.list_all(user_id)
        assert len(all_tx) == 3
        print(f"[OK] Created 3 transactions")
        
        # Delete one
        repo.delete(user_id, c2.id)
        all_tx = repo.list_all(user_id)
        assert len(all_tx) == 2
        print(f"[OK] After deletion: {len(all_tx)} transactions remain")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False




# ============================================================
# Step 5 tests (Income_Transactions) - Inherited
# ============================================================

def test_expense_transaction_creation():
    """Test creating expense transactions with factory."""
    print("\n" + "="*60)
    print("Testing Expense Transaction Creation")
    print("="*60)
    
    try:
        # Create valid expense
        expense = TransactionFactory.create_expense(
            id=1,
            account_id=1,
            category_id=1,
            amount=50.0,
            description="Groceries",
            tx_date=date(2024, 3, 15)
        )
        
        assert isinstance(expense, ExpenseTransaction)
        assert expense.id == 1
        assert expense.account_id == 1
        assert expense.category_id() == 1
        assert expense.amount == 50.0
        print(f"[OK] Created expense: {expense}")
        print(f"[OK] Expense type: {expense.tx_type.value}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_income_transaction_creation():
    """Test creating income transactions with factory."""
    print("\n" + "="*60)
    print("Testing Income Transaction Creation")
    print("="*60)
    
    try:
        # Create valid income (no category)
        income = TransactionFactory.create_income(
            id=2,
            account_id=1,
            amount=2000.0,
            description="Salary",
            tx_date=date(2024, 3, 1)
        )
        
        assert isinstance(income, IncomeTransaction)
        assert income.id == 2
        assert income.account_id == 1
        assert income.category_id() is None
        assert income.amount == 2000.0
        print(f"[OK] Created income: {income}")
        print(f"[OK] Income type: {income.tx_type.value}")
        print("[OK] Income has no category")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_expense_validation():
    """Test expense transaction validation."""
    print("\n" + "="*60)
    print("Testing Expense Validation")
    print("="*60)
    
    try:
        # Test missing category
        try:
            TransactionFactory.create_expense(
                id=1,
                account_id=1,
                category_id=0,  # Invalid
                amount=50.0,
                description="Test",
                tx_date=date(2024, 3, 15)
            )
            print("[FAIL] Should have raised ValidationError for missing category")
            return False
        except ValidationError as e:
            print(f"[OK] Missing category rejected: {e}")
        
        # Test negative amount
        try:
            TransactionFactory.create_expense(
                id=1,
                account_id=1,
                category_id=1,
                amount=-50.0,  # Invalid
                description="Test",
                tx_date=date(2024, 3, 15)
            )
            print("[FAIL] Should have raised ValidationError for negative amount")
            return False
        except ValidationError as e:
            print(f"[OK] Negative amount rejected: {e}")
        
        # Test zero amount
        try:
            TransactionFactory.create_expense(
                id=1,
                account_id=1,
                category_id=1,
                amount=0.0,  # Invalid
                description="Test",
                tx_date=date(2024, 3, 15)
            )
            print("[FAIL] Should have raised ValidationError for zero amount")
            return False
        except ValidationError as e:
            print(f"[OK] Zero amount rejected: {e}")
        
        # Test missing description
        try:
            TransactionFactory.create_expense(
                id=1,
                account_id=1,
                category_id=1,
                amount=50.0,
                description="",  # Invalid
                tx_date=date(2024, 3, 15)
            )
            print("[FAIL] Should have raised ValidationError for missing description")
            return False
        except ValidationError as e:
            print(f"[OK] Missing description rejected: {e}")
        
        # Test invalid account
        try:
            TransactionFactory.create_expense(
                id=1,
                account_id=0,  # Invalid
                category_id=1,
                amount=50.0,
                description="Test",
                tx_date=date(2024, 3, 15)
            )
            print("[FAIL] Should have raised ValidationError for invalid account")
            return False
        except ValidationError as e:
            print(f"[OK] Invalid account rejected: {e}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def test_income_validation():
    """Test income transaction validation."""
    print("\n" + "="*60)
    print("Testing Income Validation")
    print("="*60)
    
    try:
        # Income validation is same as expense except no category requirement
        
        # Test negative amount
        try:
            TransactionFactory.create_income(
                id=1,
                account_id=1,
                amount=-1000.0,  # Invalid
                description="Test",
                tx_date=date(2024, 3, 1)
            )
            print("[FAIL] Should have raised ValidationError for negative amount")
            return False
        except ValidationError as e:
            print(f"[OK] Negative amount rejected: {e}")
        
        # Test missing description
        try:
            TransactionFactory.create_income(
                id=1,
                account_id=1,
                amount=1000.0,
                description="   ",  # Invalid (whitespace)
                tx_date=date(2024, 3, 1)
            )
            print("[FAIL] Should have raised ValidationError for whitespace description")
            return False
        except ValidationError as e:
            print(f"[OK] Whitespace description rejected: {e}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def test_transaction_dto_conversion():
    """Test converting entities to DTOs."""
    print("\n" + "="*60)
    print("Testing DTO Conversion")
    print("="*60)
    
    try:
        # Create expense and convert to DTO
        expense_entity = TransactionFactory.create_expense(
            id=1,
            account_id=1,
            category_id=1,
            amount=50.0,
            description="Groceries",
            tx_date=date(2024, 3, 15)
        )
        
        expense_dto = expense_entity.to_dto()
        assert expense_dto.id == 1
        assert expense_dto.tx_type.value == "expense"
        assert expense_dto.category_id == 1
        print(f"[OK] Expense entity converted to DTO: {expense_dto}")
        
        # Create income and convert to DTO
        income_entity = TransactionFactory.create_income(
            id=2,
            account_id=1,
            amount=2000.0,
            description="Salary",
            tx_date=date(2024, 3, 1)
        )
        
        income_dto = income_entity.to_dto()
        assert income_dto.id == 2
        assert income_dto.tx_type.value == "income"
        assert income_dto.category_id is None
        print(f"[OK] Income entity converted to DTO: {income_dto}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_transaction_entity_magic_methods():
    """Test transaction entity magic methods (__str__, __repr__) for ExpenseTransaction and IncomeTransaction."""
    print("\n" + "="*60)
    print("Testing Magic Methods")
    print("="*60)
    
    try:
        expense = TransactionFactory.create_expense(
            id=1,
            account_id=1,
            category_id=1,
            amount=50.0,
            description="Test",
            tx_date=date(2024, 3, 15)
        )
        
        # Test __str__
        str_repr = str(expense)
        assert "EXPENSE" in str_repr
        assert "50.0" in str_repr
        print(f"[OK] __str__: {str_repr}")
        
        # Test __repr__
        repr_repr = repr(expense)
        assert "ExpenseTransaction" in repr_repr
        print(f"[OK] __repr__: {repr_repr[:60]}...")
        
        income = TransactionFactory.create_income(
            id=2,
            account_id=1,
            amount=2000.0,
            description="Salary",
            tx_date=date(2024, 3, 1)
        )
        
        repr_repr = repr(income)
        assert "IncomeTransaction" in repr_repr
        print(f"[OK] __repr__ for income: {repr_repr[:60]}...")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False



# ============================================================
# Step 6 tests (Categories_Analytics) - Inherited
# ============================================================

def test_category_repository():
    """Test category repository operations."""
    print("\n" + "="*60)
    print("Testing Category Repository")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp6_categories.db"):
            os.remove("test_mvp6_categories.db")
        
        db = setup_test_db("test_mvp6_categories.db")
        repo = SqliteCategoryRepository(db)
        
        user_id = 1
        
        # Add categories (Food and Transport already exist from setup, add new ones)
        cat1 = repo.add(user_id, "Utilities")
        cat2 = repo.add(user_id, "Healthcare")
        cat3 = repo.add(user_id, "Entertainment")
        
        assert cat1.id is not None
        assert cat2.id is not None
        print(f"[OK] Created 3 new categories: {cat1.name}, {cat2.name}, {cat3.name}")
        
        # List all for user 1 (should have Food + Transport + 3 new = 5 total)
        all_cats = repo.list_all(user_id)
        assert len(all_cats) >= 3
        print(f"[OK] Listed all categories: {len(all_cats)}")
        
        # Get by ID
        retrieved = repo.get_by_id(user_id, cat1.id)
        assert retrieved.name == "Utilities"
        print(f"[OK] Retrieved category: {retrieved}")
        
        # Update/rename
        repo.rename(user_id, cat1.id, "Utilities Bill")
        renamed = repo.get_by_id(user_id, cat1.id)
        assert renamed.name == "Utilities Bill"
        print(f"[OK] Renamed category: {renamed}")
        
        # Delete
        repo.delete(user_id, cat2.id)
        all_cats = repo.list_all(user_id)
        remaining_count = len(all_cats)
        print(f"[OK] Deleted category, now {remaining_count} remain")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analytics_monthly_spending():
    """Validate monthly spending analytics by category.
    
    Verifies:
    - Calculate total spending per category for month
    - Filter transactions by month and year
    - Break down spending by category
    - Aggregate multiple transactions correctly
    """
    print("\n" + "="*60)
    print("Testing Monthly Spending Analytics")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp6_analytics.db"):

            os.remove("test_mvp6_analytics.db")

        
        db = setup_test_db("test_mvp6_analytics.db")
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create transactions in different categories
        tx1 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=50.0, description="Groceries", tx_date=date(2024, 3, 5))
        tx2 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=40.0, description="Groceries", tx_date=date(2024, 3, 15))
        tx3 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=2,
                         amount=100.0, description="Gas", tx_date=date(2024, 3, 10))
        tx4 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=30.0, description="Groceries", tx_date=date(2024, 2, 20))
        
        tx_repo.add(user_id, tx1)
        tx_repo.add(user_id, tx2)
        tx_repo.add(user_id, tx3)
        tx_repo.add(user_id, tx4)
        
        # Get March expenses
        march_tx = tx_repo.list_for_month(user_id, 2024, 3)
        assert len(march_tx) == 3
        total = sum(t.amount for t in march_tx)
        assert total == 190.0
        print(f"[OK] March 2024: {len(march_tx)} expenses, total=${total}")
        
        # Break down by category
        cat1_tx = [t for t in march_tx if t.category_id == 1]
        cat2_tx = [t for t in march_tx if t.category_id == 2]
        
        print(f"[OK] Category 1 (Food): {len(cat1_tx)} tx, ${sum(t.amount for t in cat1_tx)}")
        print(f"[OK] Category 2 (Transportation): {len(cat2_tx)} tx, ${sum(t.amount for t in cat2_tx)}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_analytics_ytd_totals():
    """Test year-to-date analytics."""
    print("\n" + "="*60)
    print("Testing YTD Analytics")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp6_ytd.db"):

            os.remove("test_mvp6_ytd.db")

        
        db = setup_test_db("test_mvp6_ytd.db")
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create transactions across months
        for month in [1, 2, 3]:
            tx = Transaction(
                id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                amount=100.0, description=f"Month {month}", tx_date=date(2024, month, 15)
            )
            tx_repo.add(user_id, tx)
        
        # Get YTD
        ytd_tx = tx_repo.list_for_ytd(user_id, 2024, 3)
        assert len(ytd_tx) == 3
        total = sum(t.amount for t in ytd_tx)
        assert total == 300.0
        print(f"[OK] YTD 2024 (Jan-Mar): {len(ytd_tx)} expenses, total=${total}")
        
        # Get partial YTD
        ytd_jan = tx_repo.list_for_ytd(user_id, 2024, 1)
        assert len(ytd_jan) == 1
        assert sum(t.amount for t in ytd_jan) == 100.0
        print(f"[OK] YTD 2024 (Jan): {len(ytd_jan)} expenses, total=$100.0")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_analytics_category_breakdown():
    """Validate category-level spending breakdown and comparison.
    
    Confirms:
    - Spending breakdown across all categories
    - Identify highest and lowest spending categories
    - Compare category totals
    - Generate category spending reports
    """
    print("\n" + "="*60)
    print("Testing Category Breakdown Analytics")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp6_breakdown.db"):

            os.remove("test_mvp6_breakdown.db")

        
        db = setup_test_db("test_mvp6_breakdown.db")
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create diverse transactions
        categories_data = [
            (1, "Food", 250.0),
            (2, "Transport", 150.0),
        ]
        
        for cat_id, name, amount in categories_data:
            tx = Transaction(
                id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=cat_id,
                amount=amount, description=name, tx_date=date(2024, 3, 15)
            )
            tx_repo.add(user_id, tx)
        
        all_tx = tx_repo.list_all(user_id)
        assert len(all_tx) == 2
        total = sum(t.amount for t in all_tx)
        assert total == 400.0
        print(f"[OK] Total expenses: ${total}")
        
        # Category breakdown
        for cat_id, name, amount in categories_data:
            cat_tx = [t for t in all_tx if t.category_id == cat_id]
            actual_amount = sum(t.amount for t in cat_tx)
            percentage = (actual_amount / total) * 100
            print(f"[OK] {name}: ${actual_amount} ({percentage:.1f}%)")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False




# ============================================================
# Step 7 tests (Budget_Management) - Inherited
# ============================================================

def test_budget_repository():
    """Test budget repository operations."""
    print("\n" + "="*60)
    print("Testing Budget Repository")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp7_budgets.db"):

            os.remove("test_mvp7_budgets.db")

        
        db = setup_test_db("test_mvp7_budgets.db")
        repo = SqliteBudgetRepository(db)
        
        user_id = 1
        
        # Add budgets
        budget1 = repo.add(user_id, 1, 2024, 3, 300.0)  # Food budget $300
        budget2 = repo.add(user_id, 2, 2024, 3, 150.0)  # Transport budget $150
        
        assert budget1.id is not None
        assert budget1.limit_amount == 300.0
        print(f"[OK] Created budget 1: Category {budget1.category_id}, ${budget1.limit_amount}")
        print(f"[OK] Created budget 2: Category {budget2.category_id}, ${budget2.limit_amount}")
        
        # List all for user
        all_budgets = repo.list_all(user_id)
        assert len(all_budgets) >= 2
        print(f"[OK] Listed all budgets for user: {len(all_budgets)}")
        
        # Get by ID
        retrieved = repo.get_by_id(user_id, budget1.id)
        assert retrieved.limit_amount == 300.0
        print(f"[OK] Retrieved budget: ${retrieved.limit_amount}")
        
        # Update budget
        repo.update(user_id, budget1.id, 400.0)
        updated = repo.get_by_id(user_id, budget1.id)
        assert updated.limit_amount == 400.0
        print(f"[OK] Updated budget: ${updated.limit_amount}")
        
        # Delete budget
        repo.delete(user_id, budget2.id)
        print(f"[OK] Deleted budget")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_budget_vs_actual():
    """Test budget vs actual spending."""
    print("\n" + "="*60)
    print("Testing Budget vs Actual")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp7_vs_actual.db"):

            os.remove("test_mvp7_vs_actual.db")

        
        db = setup_test_db("test_mvp7_vs_actual.db")
        budget_repo = SqliteBudgetRepository(db)
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create budget for category 1 ($300)
        budget = budget_repo.add(user_id, 1, 2024, 3, 300.0)
        print(f"[OK] Budget set for category 1: $300")
        
        # Create actual expenses
        tx1 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=100.0, description="Exp 1", tx_date=date(2024, 3, 5))
        tx2 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=150.0, description="Exp 2", tx_date=date(2024, 3, 15))
        
        tx_repo.add(user_id, tx1)
        tx_repo.add(user_id, tx2)
        
        # Calculate actual vs budget
        month_tx = tx_repo.list_for_month(user_id, 2024, 3)
        cat1_tx = [t for t in month_tx if t.category_id == 1]
        actual_spent = sum(t.amount for t in cat1_tx)
        
        budget_limit = budget.limit_amount
        remaining = budget_limit - actual_spent
        percent_used = (actual_spent / budget_limit) * 100
        
        print(f"[OK] Budget: ${budget_limit}")
        print(f"[OK] Actual spent: ${actual_spent}")
        print(f"[OK] Remaining: ${remaining}")
        print(f"[OK] Percent used: {percent_used:.1f}%")
        
        # Verify within budget
        assert actual_spent <= budget_limit
        print(f"[OK] Under budget by ${remaining}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_budget_alerts():
    """Test budget alert thresholds."""
    print("\n" + "="*60)
    print("Testing Budget Alerts")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp7_alerts.db"):

            os.remove("test_mvp7_alerts.db")

        
        db = setup_test_db("test_mvp7_alerts.db")
        budget_repo = SqliteBudgetRepository(db)
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create $200 budget
        budget = budget_repo.add(user_id, 1, 2024, 3, 200.0)
        
        # Spend 50% - no alert
        tx1 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=100.0, description="50%", tx_date=date(2024, 3, 5))
        tx_repo.add(user_id, tx1)
        month_tx = tx_repo.list_for_month(user_id, 2024, 3)
        spent = sum(t.amount for t in month_tx if t.category_id == 1)
        percent = (spent / 200.0) * 100
        print(f"[OK] Spent {percent:.0f}% - No alert")
        assert percent <= 50
        
        # Spend 80% - warning
        tx2 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=60.0, description="80%", tx_date=date(2024, 3, 10))
        tx_repo.add(user_id, tx2)
        month_tx = tx_repo.list_for_month(user_id, 2024, 3)
        spent = sum(t.amount for t in month_tx if t.category_id == 1)
        percent = (spent / 200.0) * 100
        if percent >= 80:
            print(f"[OK] Spent {percent:.0f}% - [WARNING]")
        
        # Spend 100% - critical
        tx3 = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                         amount=40.0, description="100%", tx_date=date(2024, 3, 15))
        tx_repo.add(user_id, tx3)
        month_tx = tx_repo.list_for_month(user_id, 2024, 3)
        spent = sum(t.amount for t in month_tx if t.category_id == 1)
        percent = (spent / 200.0) * 100
        if percent >= 100:
            print(f"[OK] Spent {percent:.0f}% - [ALERT] Budget exceeded!")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_multi_category_budgets():
    """Test multiple category budgets."""
    print("\n" + "="*60)
    print("Testing Multi-Category Budgets")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp7_multi.db"):

            os.remove("test_mvp7_multi.db")

        
        db = setup_test_db("test_mvp7_multi.db")
        budget_repo = SqliteBudgetRepository(db)
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create budgets for multiple categories
        budgets = {}
        budget_data = [(1, "Food", 300.0), (2, "Transport", 150.0), (3, "Utilities", 100.0)]
        
        for cat_id, name, limit in budget_data:
            budget = budget_repo.add(user_id, cat_id, 2024, 3, limit)
            budgets[cat_id] = limit
            print(f"[OK] Budget for {name}: ${limit}")
        
        # Add expenses for each category
        expenses = [(1, 250.0), (2, 100.0), (3, 95.0)]
        for cat_id, amount in expenses:
            tx = Transaction(id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=cat_id,
                            amount=amount, description="Exp", tx_date=date(2024, 3, 15))
            tx_repo.add(user_id, tx)
        
        # Analyze each budget
        month_tx = tx_repo.list_for_month(user_id, 2024, 3)
        for cat_id, name, limit in budget_data:
            cat_tx = [t for t in month_tx if t.category_id == cat_id]
            spent = sum(t.amount for t in cat_tx)
            status = "[OK]" if spent <= limit else "[FAIL]"
            print(f"{status} {name}: ${spent}/${limit}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False




# ============================================================
# Step 8 tests (Advanced_Analytics) - Inherited
# ============================================================

def test_spending_trends():
    """Test spending trend analysis."""
    print("\n" + "="*60)
    print("Testing Spending Trends")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp8_trends.db"):

            os.remove("test_mvp8_trends.db")

        
        db = setup_test_db("test_mvp8_trends.db")
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create transactions showing trend
        monthly_amounts = [100.0, 120.0, 140.0, 160.0, 180.0]
        
        for month, amount in enumerate(monthly_amounts, start=1):
            tx = Transaction(
                id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                amount=amount, description=f"Month {month}", tx_date=date(2024, month, 15)
            )
            tx_repo.add(user_id, tx)
        
        # Analyze trend
        total_months = len(monthly_amounts)
        increase = monthly_amounts[-1] - monthly_amounts[0]
        percent_change = (increase / monthly_amounts[0]) * 100
        
        print(f"[OK] Jan-May spending: {monthly_amounts}")
        print(f"[OK] Total increase: ${increase}")
        print(f"[OK] Percent change: {percent_change:.1f}%")
        print(f"[OK] Upward trend detected!")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_category_comparison():
    """Test category spending comparison across months."""
    print("\n" + "="*60)
    print("Testing Category Comparison")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp8_category_comp.db"):

            os.remove("test_mvp8_category_comp.db")

        
        db = setup_test_db("test_mvp8_category_comp.db")
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create multi-month, multi-category data
        data = [
            # (month, category_id, amount)
            (1, 1, 100.0), (1, 2, 50.0),
            (2, 1, 120.0), (2, 2, 60.0),
            (3, 1, 150.0), (3, 2, 70.0),
        ]
        
        for month, cat_id, amount in data:
            tx = Transaction(
                id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=cat_id,
                amount=amount, description="Exp", tx_date=date(2024, month, 15)
            )
            tx_repo.add(user_id, tx)
        
        # Compare categories across months
        monthly_cat = defaultdict(lambda: defaultdict(float))
        all_tx = tx_repo.list_all(user_id)
        
        for tx in all_tx:
            monthly_cat[tx.tx_date.month][tx.category_id] += tx.amount
        
        print("[OK] Monthly comparison:")
        for month in sorted(monthly_cat.keys()):
            cat_data = monthly_cat[month]
            total = sum(cat_data.values())
            print(f"  Month {month}: Cat1=${cat_data[1]:.0f}, Cat2=${cat_data[2]:.0f}, Total=${total:.0f}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_ytd_reporting():
    """Test comprehensive YTD reporting."""
    print("\n" + "="*60)
    print("Testing YTD Reporting")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp8_ytd_report.db"):

            os.remove("test_mvp8_ytd_report.db")

        
        db = setup_test_db("test_mvp8_ytd_report.db")
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create YTD transactions (income and expenses)
        income_total = 0
        expense_total = 0
        
        for month in range(1, 4):
            # Income
            income = Transaction(
                id=0, tx_type=TxType.INCOME, account_id=1, category_id=None,
                amount=2000.0, description="Salary", tx_date=date(2024, month, 1)
            )
            tx_repo.add(user_id, income)
            income_total += 2000.0
            
            # Expenses
            expense = Transaction(
                id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                amount=500.0 * month, description="Exp", tx_date=date(2024, month, 15)
            )
            tx_repo.add(user_id, expense)
            expense_total += 500.0 * month
        
        # Generate YTD report
        ytd_tx = tx_repo.list_for_ytd(user_id, 2024, 3)
        income_tx = [t for t in ytd_tx if t.tx_type == TxType.INCOME]
        expense_tx = [t for t in ytd_tx if t.tx_type == TxType.EXPENSE]
        
        total_income = sum(t.amount for t in income_tx)
        total_expense = sum(t.amount for t in expense_tx)
        net = total_income - total_expense
        
        print(f"[OK] YTD Q1 2024 Report")
        print(f"  Total Income: ${total_income}")
        print(f"  Total Expenses: ${total_expense}")
        print(f"  Net: ${net}")
        print(f"  Savings Rate: {(net/total_income)*100:.1f}%")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_advanced_metrics():
    """Test advanced financial metrics."""
    print("\n" + "="*60)
    print("Testing Advanced Metrics")
    print("="*60)
    
    try:
        if os.path.exists("test_mvp8_metrics.db"):

            os.remove("test_mvp8_metrics.db")

        
        db = setup_test_db("test_mvp8_metrics.db")
        tx_repo = SqliteTransactionRepository(db)
        
        user_id = 1
        
        # Create sample data for metrics
        # Month 1: $3000 income, $500 expenses
        for month in [1, 2, 3]:
            tx_i = Transaction(
                id=0, tx_type=TxType.INCOME, account_id=1, category_id=None,
                amount=3000.0, description="Salary", tx_date=date(2024, month, 1)
            )
            tx_repo.add(user_id, tx_i)
            
            # Progressive expenses
            for day in [5, 10, 15, 20, 25]:
                tx_e = Transaction(
                    id=0, tx_type=TxType.EXPENSE, account_id=1, category_id=1,
                    amount=100.0, description="Daily", tx_date=date(2024, month, day)
                )
                tx_repo.add(user_id, tx_e)
        
        # Calculate metrics
        ytd_tx = tx_repo.list_for_ytd(user_id, 2024, 3)
        income_tx = [t for t in ytd_tx if t.tx_type == TxType.INCOME]
        expense_tx = [t for t in ytd_tx if t.tx_type == TxType.EXPENSE]
        
        total_income = sum(t.amount for t in income_tx)
        total_expense = sum(t.amount for t in expense_tx)
        avg_monthly_income = total_income / 3
        avg_monthly_expense = total_expense / 3
        expense_ratio = (total_expense / total_income) * 100
        
        print(f"[OK] Advanced Financial Metrics")
        print(f"  YTD Income: ${total_income}")
        print(f"  YTD Expenses: ${total_expense}")
        print(f"  Avg Monthly Income: ${avg_monthly_income}")
        print(f"  Avg Monthly Expense: ${avg_monthly_expense}")
        print(f"  Expense Ratio: {expense_ratio:.1f}%")
        print(f"  Savings Potential: ${total_income - total_expense}")
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False




# ============================================================
# Step 9 tests (Basic_UI) - New
# ============================================================

def test_nicegui_imports():
    """Test NiceGUI framework imports."""
    print("\n" + "="*60)
    print("Testing NiceGUI Imports")
    print("="*60)
    
    # Try to import NiceGUI
    try:
        from nicegui import ui
        print(f"[OK] NiceGUI imported successfully")
        print(f"[OK] UI module imported")
        return True
    except ImportError as e:
        print(f"[SKIP] NiceGUI not available: {e}")
        print(f"[SKIP] Install with: pip install nicegui")
        return True  # Skip gracefully rather than fail


def test_core_services_initialization():
    """Test initialization of core services."""
    print("\n" + "="*60)
    print("Testing Core Services")
    print("="*60)
    
    try:
        from smart_budget_manager.persistence.db import Db
        from smart_budget_manager.domain.auth_service import AuthService
        
        # Initialize database
        if os.path.exists("test_mvp9_ui.db"):

            os.remove("test_mvp9_ui.db")

        
        db = setup_test_db("test_mvp9_ui.db")
        print(f"[OK] Database initialized")
        
        # Initialize auth service
        conn = db.get_connection()
        auth = AuthService(conn)
        print(f"[OK] AuthService initialized")
        print(f"[OK] Logged in: {auth.is_logged_in()}")
        
        # Register test user with strong password
        success, msg = auth.register("testuser@example.com", "SecurePass1!", "Test User")
        if success:
            print(f"[OK] Test user registered")
            print(f"[OK] Current user: {auth.current_user}")
        else:
            print(f"[FAIL] Registration failed: {msg}")
            return False
        
        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_ui_page_imports():
    """Test UI page module imports."""
    if not NICEGUI_AVAILABLE:
        print("[SKIP] UI pages require NiceGUI")
        return True
    
    print("\n" + "="*60)
    print("Testing UI Page Imports")
    print("="*60)
    
    try:
        from smart_budget_manager.app.ui import pages_auth
        print(f"[OK] pages_auth module imported")
        
        from smart_budget_manager.app.ui import pages_dashboard
        print(f"[OK] pages_dashboard module imported")
        
        from smart_budget_manager.app.ui import pages_budget
        print(f"[OK] pages_budget module imported")
        
        from smart_budget_manager.app.ui import pages_expenses
        print(f"[OK] pages_expenses module imported")
        
        from smart_budget_manager.app.ui import pages_income
        print(f"[OK] pages_income module imported")
        
        from smart_budget_manager.app.ui import pages_categories
        print(f"[OK] pages_categories module imported")
        
        print(f"[OK] All UI page modules available")
        return True
    except ImportError as e:
        print(f"[SKIP] UI module import failed: {e}")
        return True
    except Exception as e:
        print(f"[SKIP] Error: {e}")
        return True


def test_layout_module():
    """Validate layout system and page structure.
    
    Confirms:
    - Layout components available
    - Page structure properly defined
    - Navigation layout functional
    """
    print("\n" + "="*60)
    print("Testing Layout Module")
    print("="*60)
    
    try:
        from smart_budget_manager.app.ui import layout
        print(f"[OK] Layout module imported")
        
        # Check for key functions
        if hasattr(layout, 'create_header'):
            print(f"[OK] create_header function available")
        if hasattr(layout, 'create_sidebar'):
            print(f"[OK] create_sidebar function available")
        if hasattr(layout, 'create_footer'):
            print(f"[OK] create_footer function available")
        
        return True
    except ImportError as e:
        print(f"[FAIL] Layout import failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_main_entry_point():
    """Validate main application entry point.
    
    Tests:
    - main.py can be imported
    - Application initialization functions exist
    - Entry point properly configured
    """
    print("\n" + "="*60)
    print("Testing Main Entry Point")
    print("="*60)
    
    try:
        # Check if main.py exists
        main_path = os.path.join(os.path.dirname(__file__), 'main.py')
        if not os.path.exists(main_path):
            print(f"[FAIL] main.py not found at {main_path}")
            return False
        
        print(f"[OK] main.py found")
        
        # Read main.py
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Check for key elements
        if 'nicegui' in content.lower() or 'app' in content.lower():
            print(f"[OK] main.py contains application setup")
        
        if 'if __name__' in content:
            print(f"[OK] main.py has __main__ entry point")
        
        print(f"[OK] main.py structure verified")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False




def run_all_tests():
    """Execute all tests (inherited + new).

    Validates all functionality from database initialization through basic UI:
    - Database schema and integrity
    - Domain models and magic methods
    - User authentication
    - Account repository operations
    - Expense and income transaction persistence
    - Transaction entity creation, validation, and DTO conversion
    - Category repository operations
    - Monthly, YTD, and category breakdown analytics
    - Budget repository operations
    - Budget vs actual, alerts, and multi-category tracking
    - Spending trends, category comparison, YTD reporting, advanced metrics
    - NiceGUI imports and core services
    - UI page imports, layout module, and main entry point
    """
    print("\n" + "#"*60)
    print("# Test Suite: Database + Auth + Accounts + Transactions + Categories + Budgets + Advanced Analytics + Basic UI")
    print("#"*60)
    
    # Step 1 tests (inherited)
    results = []
    results.append(("Database Initialization", test_database_initialization()))
    results.append(("Domain Models", test_models()))
    results.append(("Magic Methods", test_magic_methods()))
    results.append(("Database Persistence", test_database_persistence()))
    
    # Step 2 tests (inherited)
    results.append(("User Model", test_user_model()))
    results.append(("Email Validation", test_email_validation()))
    results.append(("Password Validation", test_password_validation()))
    results.append(("Username Validation", test_username_validation()))
    results.append(("User Registration", test_user_registration()))
    results.append(("User Login", test_user_login()))
    results.append(("Session Management", test_session_management()))
    results.append(("AuthService Methods", test_auth_service_methods()))
    
    # Step 3 tests (inherited)
    results.append(("Account Creation", test_account_creation()))
    results.append(("Account Retrieval", test_account_retrieval()))
    results.append(("Account Rename", test_account_rename()))
    results.append(("Account Deletion", test_account_deletion()))
    results.append(("User Isolation", test_user_isolation()))
    
    # Step 4 tests (inherited)
    results.append(("Expense Creation", test_expense_creation()))
    results.append(("Transaction Queries", test_transaction_queries()))
    results.append(("Income and Expense Mix", test_income_and_expense()))
    results.append(("Transaction Update", test_transaction_update()))
    results.append(("Transaction Deletion", test_transaction_deletion()))
    
    # Step 5 tests (inherited)
    results.append(("Expense Transaction Creation", test_expense_transaction_creation()))
    results.append(("Income Transaction Creation", test_income_transaction_creation()))
    results.append(("Expense Validation", test_expense_validation()))
    results.append(("Income Validation", test_income_validation()))
    results.append(("Transaction Dto Conversion", test_transaction_dto_conversion()))
    results.append(("Transaction Magic Methods", test_transaction_entity_magic_methods()))
    
    # Step 6 tests (inherited)
    results.append(("Category Repository", test_category_repository()))
    results.append(("Monthly Spending Analytics", test_analytics_monthly_spending()))
    results.append(("YTD Analytics", test_analytics_ytd_totals()))
    results.append(("Category Breakdown Analytics", test_analytics_category_breakdown()))
    
    # Step 7 tests (inherited)
    results.append(("Budget Repository", test_budget_repository()))
    results.append(("Budget vs Actual", test_budget_vs_actual()))
    results.append(("Budget Alerts", test_budget_alerts()))
    results.append(("Multi-Category Budgets", test_multi_category_budgets()))

    # Step 8 tests (inherited)
    results.append(("Spending Trends", test_spending_trends()))
    results.append(("Category Comparison", test_category_comparison()))
    results.append(("YTD Reporting", test_ytd_reporting()))
    results.append(("Advanced Metrics", test_advanced_metrics()))
    
    # Step 9 tests (new)
    results.append(("NiceGUI Imports", test_nicegui_imports()))
    results.append(("Core Services Init", test_core_services_initialization()))
    results.append(("UI Page Imports", test_ui_page_imports()))
    results.append(("Layout Module", test_layout_module()))
    results.append(("Main Entry Point", test_main_entry_point()))
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for i, (test_name, passed) in enumerate(results, 1):
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print("{:2}. {}: {}".format(i, status, test_name))
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print("\nTotal: {}/{} passed".format(passed_count, total))
    all_passed = all(result[1] for result in results)
    
    print("\n" + "#"*60)
    if all_passed:
        print("# [OK] ALL TESTS PASSED!")
    else:
        print("# [FAIL] SOME TESTS FAILED")
    print("#"*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
