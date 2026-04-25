"""Authentication service for user management.

Provides login and registration functionality with persistent user storage
using SQLite database. Includes comprehensive input validation for security.
"""

import hashlib
import hmac
import os
import sqlite3
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from ..domain.validators import validate_email, validate_password, validate_username, sanitize_input
from ..data_access.seed import seed_new_user

if TYPE_CHECKING:
    from ..data_access.db import Db


def _hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a random salt.

    Returns:
        str: Hex-encoded 'salt:key' string suitable for storage.
    """
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash.

    Args:
        password (str): Plaintext password to verify.
        stored_hash (str): Stored 'salt:key' string from database.

    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(key, bytes.fromhex(key_hex))
    except (ValueError, AttributeError):
        return False


@dataclass(frozen=True)
class User:
    """User entity for authentication.

    Immutable user representation with unique email identifier and optional username.

    Attributes:
        id (int): Unique user identifier.
        email (str): User email address (unique).
        username (str): Optional display name for the user.
    """

    id: int
    email: str
    username: str = ""

    def __str__(self) -> str:
        display_name = self.username or self.email.split("@")[0]
        return f"{display_name} ({self.email})"

    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}', username='{self.username}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.email == other.email

    def __hash__(self) -> int:
        return hash(self.email)


class AuthService:
    """Service for user authentication and registration.

    Manages user login and signup operations with persistent SQLite storage.
    Users are saved to the database and persist across app restarts.
    """

    def __init__(self, db: "Db") -> None:
        """Initialize authentication service with database storage.

        Args:
            db (Db): Database manager instance. The service uses the shared
                connection provided by the Db instance, guaranteeing that all
                writes are immediately visible to every other service that uses
                the same Db object.
        """
        self._db = db
        self._current_user: Optional[User] = None

    @property
    def _conn(self) -> sqlite3.Connection:
        """Return the shared database connection from the Db manager."""
        return self._db.get_connection()

    @property
    def current_user(self) -> Optional[User]:
        """Get currently logged-in user (read-only)."""
        return self._current_user

    def __str__(self) -> str:
        if self._current_user:
            return f"AuthService (logged in as {self._current_user})"
        return "AuthService (not logged in)"

    def __repr__(self) -> str:
        return f"AuthService(current_user={self._current_user!r})"

    def register(self, email: str, password: str, username: str = "") -> tuple[bool, str]:
        """Register a new user with mandatory email and strong password.

        Args:
            email (str): User email address (unique identifier).
            password (str): Password (must meet security requirements).
            username (str): Optional display name for the user.

        Returns:
            tuple[bool, str]: (success, message).
        """
        email = sanitize_input(email)
        password = sanitize_input(password)
        username = sanitize_input(username)

        email_valid, email_error = validate_email(email)
        if not email_valid:
            return False, email_error

        password_valid, password_error = validate_password(password)
        if not password_valid:
            return False, password_error

        username_valid, username_error = validate_username(username)
        if not username_valid:
            return False, username_error

        try:
            cursor = self._conn.cursor()

            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "Email already registered"

            username_display = username or email.split("@")[0]
            cursor.execute(
                "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
                (email, username_display, _hash_password(password)),
            )
            user_id = cursor.lastrowid

            # Seed default accounts and categories for the new user
            seed_new_user(self._conn, user_id)

            self._conn.commit()

            self._current_user = User(id=user_id, email=email, username=username_display)
            return True, "Registration successful"
        except sqlite3.IntegrityError:
            self._conn.rollback()
            return False, "Email already registered"
        except sqlite3.Error as e:
            self._conn.rollback()
            return False, f"Database error: {str(e)}"

    def login(self, email: str, password: str) -> tuple[bool, str]:
        """Authenticate user with email and password.

        Args:
            email (str): User email to authenticate.
            password (str): Password to verify.

        Returns:
            tuple[bool, str]: (success, message).
        """
        email = sanitize_input(email)
        password = sanitize_input(password)

        email_valid, email_error = validate_email(email)
        if not email_valid:
            return False, email_error

        if not password:
            return False, "Password is required"

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, email, username, password_hash FROM users WHERE email = ?",
                (email,),
            )
            row = cursor.fetchone()

            if not row or not _verify_password(password, row[3]):
                return False, "Invalid email or password"

            user_id, user_email, user_username = row[0], row[1], row[2]
            self._current_user = User(
                id=user_id,
                email=user_email,
                username=user_username or "",
            )
            return True, "Login successful"
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

    def logout(self) -> None:
        """Log out current user by clearing session state."""
        self._current_user = None

    def get_current_user(self) -> Optional[User]:
        """Get currently logged-in user.

        Deprecated:
            Use the current_user property instead for better encapsulation.
        """
        return self._current_user

    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self._current_user is not None
