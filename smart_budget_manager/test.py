#!/usr/bin/env python3
"""Comprehensive Test Suite """

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_budget_manager'))

from persistence.db import Db
from domain.auth_service import AuthService, User
from domain.exceptions import AuthenticationError
from domain.validators import (
    validate_email, validate_password, validate_username, 
    sanitize_input, validate_all_inputs
)


def test_user_model():
    """Test User model and magic methods."""
    print("\n" + "="*60)
    print("Testing User Model")
    print("="*60)
    
    try:
        user1 = User(id=1, email="john@example.com", username="John")
        user2 = User(id=2, email="jane@example.com", username="Jane")
        user3 = User(id=3, email="john@example.com", username="Johnny")
        
        # Test __str__
        print(f"✓ __str__: {user1}")
        
        # Test __repr__
        print(f"✓ __repr__: {repr(user1)}")
        
        # Test __eq__ (same email = same user)
        assert user1 == user3
        assert not (user1 == user2)
        print("✓ __eq__: Equality based on email works")
        
        # Test __hash__
        user_set = {user1, user2, user3}
        assert len(user_set) == 2  # user1 and user3 have same email
        print("✓ __hash__: Can be used in sets/dicts")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_email_validation():
    """Test email validation rules."""
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
                print(f"✓ {description}: '{email}'")
            else:
                print(f"✗ {description}: '{email}' - Expected {expected}, got {is_valid}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_password_validation():
    """Test password security validation rules."""
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
                print(f"✓ {description}: {len(password)} chars")
            else:
                print(f"✗ {description}: Expected {expected}, got {is_valid} - {error}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_username_validation():
    """Test username validation rules."""
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
                print(f"✓ {description}: '{username}'")
            else:
                print(f"✗ {description}: Expected {expected}, got {is_valid}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_user_registration():
    """Test user registration functionality with new validation."""
    # Clean test database
    db_file = "test_register.db"
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
        print(f"✓ Successfully registered: {auth.current_user}")
        
        # Test duplicate registration
        success, msg = auth.register("alice@example.com", "AnotherPass1!", "Alice2")
        assert not success
        print(f"✓ Duplicate registration blocked: {msg}")
        
        # Test missing email
        success, msg = auth.register("", "SecurePass1!", "Bob")
        assert not success
        print(f"✓ Missing email rejected: {msg}")
        
        # Test missing password
        success, msg = auth.register("bob@example.com", "", "Bob")
        assert not success
        print(f"✓ Missing password rejected: {msg}")
        
        # Test invalid email
        success, msg = auth.register("invalid-email", "SecurePass1!", "Bob")
        assert not success
        print(f"✓ Invalid email rejected: {msg}")
        
        # Test weak password - too short
        success, msg = auth.register("bob@example.com", "Short1!", "Bob")
        assert not success
        assert "at least 8" in msg.lower()
        print(f"✓ Short password rejected: {msg}")
        
        # Test weak password - no uppercase
        success, msg = auth.register("bob@example.com", "lowercase1!", "Bob")
        assert not success
        assert "uppercase" in msg.lower()
        print(f"✓ No uppercase rejected: {msg}")
        
        # Test weak password - no lowercase
        success, msg = auth.register("bob@example.com", "UPPERCASE1!", "Bob")
        assert not success
        assert "lowercase" in msg.lower()
        print(f"✓ No lowercase rejected: {msg}")
        
        # Test weak password - no digit
        success, msg = auth.register("bob@example.com", "NoDigit!", "Bob")
        assert not success
        assert "number" in msg.lower()
        print(f"✓ No digit rejected: {msg}")
        
        # Test weak password - no special character
        success, msg = auth.register("bob@example.com", "NoSpecial1", "Bob")
        assert not success
        assert "special" in msg.lower()
        print(f"✓ No special character rejected: {msg}")
        
        # Test invalid username
        success, msg = auth.register("charlie@example.com", "SecurePass1!", "Invalid@Name")
        assert not success
        assert "username" in msg.lower()
        print(f"✓ Invalid username rejected: {msg}")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_user_login():
    """Test user login functionality."""
    print("\n" + "="*60)
    print("Testing User Login")
    print("="*60)
    
    try:
        db = Db("test_login.db")
        db.initialize()
        auth = AuthService(db.get_connection())
        
        # Register user first
        auth.register("bob@example.com", "SecurePass1!", "Bob")
        auth.logout()
        print("✓ User registered and logged out")
        
        # Test successful login
        success, msg = auth.login("bob@example.com", "SecurePass1!")
        assert success, f"Login failed: {msg}"
        assert auth.is_logged_in()
        print(f"✓ Successfully logged in: {auth.current_user}")
        
        # Test wrong password
        auth.logout()
        success, msg = auth.login("bob@example.com", "WrongPassword1!")
        assert not success
        assert not auth.is_logged_in()
        print(f"✓ Wrong password rejected: {msg}")
        
        # Test user not found
        success, msg = auth.login("nonexistent@example.com", "SecurePass1!")
        assert not success
        assert not auth.is_logged_in()
        print(f"✓ Nonexistent user rejected: {msg}")
        
        # Test missing credentials
        success, msg = auth.login("", "")
        assert not success
        print(f"✓ Missing credentials rejected: {msg}")
        
        # Test invalid email format on login
        success, msg = auth.login("not-an-email", "SecurePass1!")
        assert not success
        print(f"✓ Invalid email format on login rejected: {msg}")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_session_management():
    """Test login/logout session management."""
    # Clean test database
    if os.path.exists("test_session.db"):
        os.remove("test_session.db")
    
    print("\n" + "="*60)
    print("Testing Session Management")
    print("="*60)
    
    try:
        db = Db("test_session.db")
        db.initialize()
        auth = AuthService(db.get_connection())
        
        # Test not logged in initially
        assert not auth.is_logged_in()
        assert auth.current_user is None
        print("✓ Initially not logged in")
        
        # Register and verify logged in
        auth.register("charlie@example.com", "SecurePass1!", "Charlie")
        assert auth.is_logged_in()
        assert auth.current_user is not None
        print(f"✓ Logged in after registration: {auth.current_user}")
        
        # Logout
        auth.logout()
        assert not auth.is_logged_in()
        assert auth.current_user is None
        print("✓ Successfully logged out")
        
        # Login again
        success, msg = auth.login("charlie@example.com", "SecurePass1!")
        assert success and auth.is_logged_in()
        print("✓ Successfully logged in again")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_auth_service_methods():
    """Test AuthService string methods."""
    print("\n" + "="*60)
    print("Testing AuthService Methods")
    print("="*60)
    
    try:
        db = Db("test_methods.db")
        db.initialize()
        auth = AuthService(db.get_connection())
        
        # Test __str__ when not logged in
        str_repr = str(auth)
        assert "not logged in" in str_repr.lower()
        print(f"✓ __str__ (not logged in): {str_repr}")
        
        # Login and test __str__
        auth.register("dave@example.com", "SecurePass1!", "Dave")
        str_repr = str(auth)
        print(f"✓ __str__ (logged in): {str_repr}")
        
        # Test __repr__
        repr_str = repr(auth)
        assert "AuthService" in repr_str
        print(f"✓ __repr__ working")
        
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_database_initialization():
    """Test database initialization and schema creation."""
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
        print(f"✗ Error: {e}")
        return False

def test_models():
    """Test all domain models."""
    print("\n" + "="*60)
    print("Testing Domain Models")
    print("="*60)
    
    try:
        # Test TxType enum
        from domain.models import TxType, Account, Category, Transaction, MonthlyBudget
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
        from datetime import date
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
        print(f"✓ MonthlyBudget model: {budget}")
        
        # Test immutability (frozen dataclasses)
        try:
            account.name = "Changed"
            print("✗ Account should be immutable (frozen)")
            return False
        except Exception:
            print("✓ Account is immutable (frozen)")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_magic_methods():
    """Test OOP magic methods."""
    print("\n" + "="*60)
    print("Testing Magic Methods")
    print("="*60)
    
    try:
        from domain.models import Account, Category
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
        print(f"✗ Error: {e}")
        return False

def test_database_persistence():
    """Test that data persists correctly in database."""
    print("\n" + "="*60)
    print("Testing Database Persistence")
    print("="*60)
    
    try:
        # Clean up old test database
        import os
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
        print(f"✗ Error: {e}")
        return False

def run_all_tests():
    """Run all tests )."""
    print("\n" + "#"*60)
    print("# Complete Test Suite")
    print("#"*60)
    
    results = []
    # tests
    results.append(("User Model", test_user_model()))
    results.append(("Email Validation", test_email_validation()))
    results.append(("Password Validation", test_password_validation()))
    results.append(("Username Validation", test_username_validation()))
    results.append(("User Registration", test_user_registration()))
    results.append(("User Login", test_user_login()))
    results.append(("Session Management", test_session_management()))
    results.append(("AuthService Methods", test_auth_service_methods()))
    # Database/Models tests
    results.append(("Database Initialization", test_database_initialization()))
    results.append(("Domain Models", test_models()))
    results.append(("Magic Methods", test_magic_methods()))
    results.append(("Database Persistence", test_database_persistence()))
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "#"*60)
    if all_passed:
        print("# ✓ ALL TESTS PASSED!")
    else:
        print("# ✗ SOME TESTS FAILED")
    print("#"*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
