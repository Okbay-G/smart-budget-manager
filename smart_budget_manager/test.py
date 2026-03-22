#!/usr/bin/env python3
"""Comprehensive Test Suite for : Database and Models"""

import sys
import os
from datetime import date

# Add smart_budget_manager to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_budget_manager'))

from persistence.db import Db
from domain.models import TxType, Account, Category, Transaction, MonthlyBudget


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
    """Run all tests."""
    print("\n" + "#"*60)
    print("# Database and Models - Complete Test Suite")
    print("#"*60)
    
    results = []
    results.append(("Database Initialization", test_database_initialization()))
    results.append(("Domain Models", test_models()))
    results.append(("Magic Methods", test_magic_methods()))
    results.append(("Database Persistence", test_database_persistence()))
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "#"*60)
    if all_passed:
        print("# [SUCCESS] ALL TESTS PASSED!")
    else:
        print("# [FAILURE] SOME TESTS FAILED")
    print("#"*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
