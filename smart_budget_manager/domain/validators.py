"""Input validation module for security and data integrity.

Provides validation functions for email format, password strength,
and general input sanitization to prevent common vulnerabilities.

Functions:
    validate_email: Validate email format.
    validate_password: Validate password meets security requirements.
    validate_username: Validate username format and length.
    sanitize_input: Sanitize string input (strip whitespace).
"""

import re
from typing import Tuple


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format according to RFC 5322 simplified rules.
    
    Args:
        email (str): Email address to validate.
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message).
        
    Validation rules:
        - Not empty
        - Contains @ symbol
        - Has domain with at least one dot
        - Valid characters (alphanumeric, dots, hyphens, underscores)
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"
    
    email = email.strip().lower()
    
    if len(email) > 254:
        return False, "Email is too long (max 254 characters)"
    
    if len(email) < 5:
        return False, "Email is too short (min 5 characters)"
    
    # RFC 5322 simplified regex pattern
    pattern = r'^[a-zA-Z0-9._+%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    # Check for consecutive dots
    if ".." in email:
        return False, "Email cannot contain consecutive dots"
    
    # Check valid structure
    if email.startswith(".") or email.endswith("."):
        return False, "Email cannot start or end with a dot"
    
    if email.startswith("@") or email.endswith("@"):
        return False, "Invalid email format"
    
    local_part, domain = email.split("@")[0], email.split("@")[1]
    
    if not local_part or len(local_part) > 64:
        return False, "Invalid email local part"
    
    # Check local part doesn't start or end with dot
    if local_part.startswith(".") or local_part.endswith("."):
        return False, "Invalid email local part"
    
    if not domain:
        return False, "Invalid email domain"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password meets security requirements.
    
    Args:
        password (str): Password to validate.
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message).
        
    Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit (0-9)
        - At least one special character (!@#$%^&*-_=+)
        - No leading/trailing whitespace
        - No excessive length (max 128 characters)
    """
    if not password or not isinstance(password, str):
        return False, "Password must be a non-empty string"
    
    if password != password.strip():
        return False, "Password cannot start or end with whitespace"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    # Check for at least one special character
    special_char_pattern = r'[!@#$%^&*\-_=+\[\]{};:\'",.<>?/\\|`~]'
    if not re.search(special_char_pattern, password):
        return False, "Password must contain at least one special character (!@#$%^&*-_=+, etc.)"
    
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format and length.
    
    Args:
        username (str): Username to validate.
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message).
        
    Requirements:
        - Optional (can be empty)
        - If provided: 1-50 characters
        - Alphanumeric, spaces, hyphens, and underscores only
        - No leading/trailing whitespace
    """
    if not username:
        return True, ""  # Username is optional
    
    if not isinstance(username, str):
        return False, "Username must be a string"
    
    if username != username.strip():
        return False, "Username cannot start or end with whitespace"
    
    if len(username) < 1 or len(username) > 50:
        return False, "Username must be between 1 and 50 characters"
    
    # Allow alphanumeric, spaces, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', username):
        return False, "Username can only contain letters, numbers, spaces, hyphens, and underscores"
    
    # Check for excessive spaces
    if "  " in username:
        return False, "Username cannot contain multiple consecutive spaces"
    
    return True, ""


def sanitize_input(value: str) -> str:
    """Sanitize string input by stripping whitespace.
    
    Args:
        value (str): Input string to sanitize.
        
    Returns:
        str: Sanitized input (stripped).
        
    Note:
        This function handles None and empty values gracefully.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value).strip()
    return value.strip()


def validate_all_inputs(email: str, password: str, username: str = "") -> Tuple[bool, str]:
    """Validate all user inputs at once.
    
    Args:
        email (str): Email address.
        password (str): Password.
        username (str): Optional username.
        
    Returns:
        Tuple[bool, str]: (all_valid, error_message if invalid).
    """
    # Sanitize inputs
    email = sanitize_input(email)
    password = sanitize_input(password)
    username = sanitize_input(username)
    
    # Validate email
    email_valid, email_error = validate_email(email)
    if not email_valid:
        return False, email_error
    
    # Validate password
    password_valid, password_error = validate_password(password)
    if not password_valid:
        return False, password_error
    
    # Validate username
    username_valid, username_error = validate_username(username)
    if not username_valid:
        return False, username_error
    
    return True, ""
