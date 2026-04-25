"""Default data seeding for new users.

Provides seed_new_user() which inserts default accounts and categories
for a newly registered user so the application is immediately usable.
This keeps seeding logic in the persistence layer, separate from auth logic.
"""

import sqlite3

_DEFAULT_ACCOUNTS = ["Checking", "Savings", "Cash", "Credit Card"]

_DEFAULT_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Utilities",
    "Entertainment",
    "Shopping",
    "Health",
    "Rent/Mortgage",
    "Savings",
    "Other",
]


def seed_new_user(conn: sqlite3.Connection, user_id: int) -> None:
    """Insert default accounts and categories for a newly registered user.

    Executes within the caller's transaction — does NOT commit.

    Args:
        conn: Active SQLite connection (must have an open transaction).
        user_id: ID of the newly created user.
    """
    cursor = conn.cursor()
    for name in _DEFAULT_ACCOUNTS:
        cursor.execute(
            "INSERT INTO accounts (user_id, name) VALUES (?, ?)",
            (user_id, name),
        )
    for name in _DEFAULT_CATEGORIES:
        cursor.execute(
            "INSERT INTO categories (user_id, name) VALUES (?, ?)",
            (user_id, name),
        )
