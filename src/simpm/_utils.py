"""
Internal utility functions for the SimPM package.

These functions are intended for internal use only and are not part of the public API.
"""

from typing import Any

def _swap_dict_keys_values(original_dict: dict[Any,Any]) -> dict[Any,Any]:
    """Swaps the keys and values of a dictionary. Usable for large dictionaries

    Args:
        original_dict (dict): Original dictionary

    Returns:
        dict: Swapped dictionary
    """
    swapped_dict = {}
    for key, value in original_dict.items():
        swapped_dict[value] = key
    return swapped_dict
