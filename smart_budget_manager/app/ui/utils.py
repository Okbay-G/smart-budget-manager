"""Shared UI utility helpers.

Provides common formatting and helper functions used across all UI pages
to avoid duplication and ensure consistent presentation.

Functions:
    money: Format a numeric value as a CHF currency string.
"""

from __future__ import annotations


def money(v: float) -> str:
    """Format a numeric value as a CHF currency string.

    Args:
        v (float): Value to format.

    Returns:
        str: Formatted currency string (e.g., "CHF 1,234.56").
    """
    return f"CHF {v:,.2f}"
