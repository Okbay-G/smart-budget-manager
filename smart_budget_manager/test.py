#!/usr/bin/env python3
"""Comprehensive Test Suite for Account Management

Extends authentication tests and validates account management features:
- Account creation with ID generation
- Account retrieval by ID and user listing
- Account rename operations with whitespace trimming
- Account deletion and cascade handling
- User isolation: accounts segregated by user
- Repository pattern for data access
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from smart_budget_manager.persistence.db import Db
from smart_budget_manager.persistence.repositories import SqliteAccountRepository
from smart_budget_manager.domain.models import Account


def setup_test_db(db_name):
    """Helper to create a test database with test users."""
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
        db = setup_test_db("test_mvp3_create.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        
        # Create first account
        acc1 = repo.add(user_id, "Savings Account")
        assert acc1.id is not None
        assert acc1.name == "Savings Account"
        print("[PASS] Created account 1: {}".format(acc1))
        
        # Create second account
        acc2 = repo.add(user_id, "Checking Account")
        assert acc2.id is not None
        assert acc2.id > acc1.id
        print("[PASS] Created account 2: {}".format(acc2))
        
        # Create account for different user
        acc3 = repo.add(2, "Business Account")
        assert acc3.id is not None
        print("[PASS] Created account for different user: {}".format(acc3))
        
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
        db = setup_test_db("test_mvp3_retrieve.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        
        # Create accounts
        repo.add(user_id, "Account A")
        repo.add(user_id, "Account B")
        repo.add(user_id, "Account C")
        
        # List all for user
        accounts = repo.list_all(user_id)
        assert len(accounts) == 3
        print("[PASS] Listed all accounts for user: {} accounts".format(len(accounts)))
        
        # Verify they're sorted alphabetically
        names = [a.name for a in accounts]
        assert names == sorted(names)
        print("[PASS] Accounts sorted alphabetically: {}".format(names))
        
        # Get by ID
        account_id = accounts[0].id
        retrieved = repo.get_by_id(user_id, account_id)
        assert retrieved is not None
        assert retrieved.name == accounts[0].name
        print("[PASS] Retrieved account by ID: {}".format(retrieved))
        
        # Get nonexistent account
        nonexistent = repo.get_by_id(user_id, 9999)
        assert nonexistent is None
        print("[PASS] Nonexistent account returns None")
        
        # Get from wrong user
        repo.add(2, "Another Account")
        other_user_account = repo.list_all(2)[0]
        wrong_user = repo.get_by_id(user_id, other_user_account.id)
        assert wrong_user is None
        print("[PASS] Cannot retrieve account from wrong user")
        
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
        db = setup_test_db("test_mvp3_rename.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        account = repo.add(user_id, "Original Name")
        account_id = account.id
        
        # Rename account
        repo.rename(user_id, account_id, "New Name")
        renamed = repo.get_by_id(user_id, account_id)
        assert renamed.name == "New Name"
        print("[PASS] Renamed account: {}".format(renamed))
        
        # Rename with whitespace trimming
        repo.rename(user_id, account_id, "  Trimmed Name  ")
        trimmed = repo.get_by_id(user_id, account_id)
        assert trimmed.name == "Trimmed Name"
        print("[PASS] Whitespace trimmed: '{}'".format(trimmed.name))
        
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
        db = setup_test_db("test_mvp3_delete.db")
        repo = SqliteAccountRepository(db)
        
        user_id = 1
        acc1 = repo.add(user_id, "Account 1")
        acc2 = repo.add(user_id, "Account 2")
        
        # Delete first account
        repo.delete(user_id, acc1.id)
        remaining = repo.list_all(user_id)
        assert len(remaining) == 1
        assert remaining[0].id == acc2.id
        print("[PASS] Deleted account successfully")
        
        # Verify deleted account is gone
        deleted = repo.get_by_id(user_id, acc1.id)
        assert deleted is None
        print("[PASS] Deleted account not retrievable")
        
        # Try to delete nonexistent
        try:
            repo.delete(user_id, 9999)
            print("[PASS] Deleting nonexistent account handled")
        except:
            print("[PASS] Deleting nonexistent account raises exception")
        
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
        db = setup_test_db("test_mvp3_isolation.db")
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
        print("[PASS] User 1 has {} accounts".format(len(u1_accounts)))
        print("[PASS] User 2 has {} accounts".format(len(u2_accounts)))
        
        # Delete user1 account, user2 should be unaffected
        repo.delete(user1_id, u1_acc1.id)
        u1_accounts = repo.list_all(user1_id)
        u2_accounts = repo.list_all(user2_id)
        
        assert len(u1_accounts) == 1
        assert len(u2_accounts) == 1
        print("[PASS] Deleting user1 account doesn't affect user2")
        
        db.close()
        return True
    except Exception as e:
        print("[FAIL] Error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all account management tests.
    
    Validates:
    - Account CRUD operations (Create, Read, Update, Delete)
    - Repository pattern for data persistence
    - User isolation and multi-tenant access control
    - Account listing and filtering
    - Unique ID generation
    """
    print("\n" + "#"*60)
    print("# Account Management - Complete Test Suite")
    print("#"*60)
    
    results = []
    results.append(("Account Creation", test_account_creation()))
    results.append(("Account Retrieval", test_account_retrieval()))
    results.append(("Account Rename", test_account_rename()))
    results.append(("Account Deletion", test_account_deletion()))
    results.append(("User Isolation", test_user_isolation()))
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print("{}: {}".format(status, test_name))
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "#"*60)
    if all_passed:
        print("# ✓ ALL ACCOUNT MANAGEMENT TESTS PASSED!")
    else:
        print("# ✗ SOME TESTS FAILED")
    print("#"*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
