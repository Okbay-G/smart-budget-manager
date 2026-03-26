"""Authentication service for user management.

Provides login and registration functionality with persistent user storage
using SQLite database. Includes comprehensive input validation for security.
"""

import sqlite3
from dataclasses import dataclass
from typing import Optional

from .exceptions import AuthenticationError
from .validators import validate_email, validate_password, validate_username, sanitize_input


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
        """Return user display name and email.
        
        Returns:
            str: Formatted user representation.
        """
        display_name = self.username or self.email.split("@")[0]
        return f"{display_name} ({self.email})"

    def __repr__(self) -> str:
        """Return detailed user representation.
        
        Returns:
            str: Detailed object representation.
        """
        return f"User(id={self.id}, email='{self.email}', username='{self.username}')"

    def __eq__(self, other: object) -> bool:
        """Compare users by email (unique identifier).
        
        Args:
            other: Object to compare with.
            
        Returns:
            bool: True if both are User objects with same email.
        """
        if not isinstance(other, User):
            return NotImplemented
        return self.email == other.email

    def __hash__(self) -> int:
        """Return hash based on email.
        
        Returns:
            int: Hash of email (unique identifier).
        """
        return hash(self.email)


class AuthService:
    """Service for user authentication and registration.
    
    Manages user login and signup operations with persistent SQLite storage.
    Users are saved to the database and persist across app restarts.
    Provides encapsulated access to database connection and current user state.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize authentication service with database storage.

        Args:
            db_connection (sqlite3.Connection): SQLite database connection.
        """
        self._conn = db_connection
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        """Get currently logged-in user (read-only).

        Returns:
            Optional[User]: Current user or None if not logged in.
        """
        return self._current_user

    def __str__(self) -> str:
        """Return service status information.
        
        Returns:
            str: Service status with current user info.
        """
        if self._current_user:
            return f"AuthService (logged in as {self._current_user})"
        return "AuthService (not logged in)"

    def __repr__(self) -> str:
        """Return detailed service representation.
        
        Returns:
            str: Detailed object representation.
        """
        return f"AuthService(current_user={self._current_user!r})"

    def register(self, email: str, password: str, username: str = "") -> tuple[bool, str]:
        """Register a new user with mandatory email and strong password.

        Args:
            email (str): User email address (unique identifier).
            password (str): Password (must meet security requirements).
            username (str): Optional display name for the user.

        Returns:
            tuple[bool, str]: (success, message).
            
        Validation rules:
            - Email: Valid format with domain
            - Password: Min 8 chars, uppercase, lowercase, digit, special char
            - Username: Optional, alphanumeric with spaces/hyphens/underscores
        """
        # Sanitize inputs
        email = sanitize_input(email)
        password = sanitize_input(password)
        username = sanitize_input(username)
        
        # Validate email format
        email_valid, email_error = validate_email(email)
        if not email_valid:
            return False, email_error
        
        # Validate password strength
        password_valid, password_error = validate_password(password)
        if not password_valid:
            return False, password_error
        
        # Validate username format
        username_valid, username_error = validate_username(username)
        if not username_valid:
            return False, username_error
        
        try:
            cursor = self._conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "Email already registered"
            
            # Insert new user
            username_display = username or email.split("@")[0]
            cursor.execute(
                "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
                (email, username_display, password)  # In production, hash the password!
            )
            self._conn.commit()
            
            user_id = cursor.lastrowid
            self._current_user = User(id=user_id, email=email, username=username_display)
            return True, f"Registered successfully as {username_display}"
        
        except sqlite3.Error as e:
            return False, f"Registration failed: {str(e)}"

    def login(self, email: str, password: str) -> tuple[bool, str]:
        """Log in existing user with email and password.

        Args:
            email (str): User email address.
            password (str): User password.

        Returns:
            tuple[bool, str]: (success, message).
            
        Note:
            Validates input format before querying database.
        """
        # Sanitize inputs
        email = sanitize_input(email)
        password = sanitize_input(password)
        
        # Validate email format
        email_valid, email_error = validate_email(email)
        if not email_valid:
            return False, email_error
        
        if not password:
            return False, "Password is required"
        
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT id, email, username, password_hash FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            
            if not row:
                return False, "User not found or invalid credentials"
            
            user_id, user_email, user_username, stored_password = row
            
            # Simple password check (in production, use proper hashing!)
            if password != stored_password:
                return False, "User not found or invalid credentials"
            
            self._current_user = User(id=user_id, email=user_email, username=user_username)
            return True, f"Logged in as {user_username}"
        
        except sqlite3.Error as e:
            return False, f"Login failed: {str(e)}"

    def logout(self) -> None:
        """Log out current user."""
        self._current_user = None

    def is_logged_in(self) -> bool:
        """Check if user is currently logged in.
        
        Returns:
            bool: True if user is logged in, False otherwise.
        """
        return self._current_user is not None
