# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Security Utilities Module

Provides input validation, safe file operations, and security event logging for Satya.
"""

import os
import re
import logging
from typing import Any

SECURITY_LOG_FILE = os.path.join(os.path.dirname(__file__), 'security.log')
logging.basicConfig(
    filename=SECURITY_LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def validate_username(username: str) -> bool:
    """
    Validate a username (alphanumeric, 3-32 chars).
    Args:
        username (str): The username to validate
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(r'^[A-Za-z0-9_]{3,32}$', username))

def sanitize_filepath(filepath: str, base_dir: str) -> str:
    """
    Sanitize a file path to prevent path traversal.
    Args:
        filepath (str): The user-supplied file path
        base_dir (str): The base directory to restrict access
    Returns:
        str: The safe, absolute file path
    Raises:
        ValueError: If the path is unsafe
    """
    abs_path = os.path.abspath(os.path.join(base_dir, filepath))
    if not abs_path.startswith(os.path.abspath(base_dir)):
        raise ValueError("Unsafe file path detected.")
    return abs_path

def log_security_event(message: str) -> None:
    """
    Log a security-relevant event.
    Args:
        message (str): The message to log
    """
    logging.info(message)

def validate_content_input(data: Any) -> bool:
    """
    Basic validation for content input (dict or str, not too large).
    Args:
        data (Any): The input data
    Returns:
        bool: True if valid, False otherwise
    """
    if isinstance(data, dict):
        return len(str(data)) < 100_000  # 100KB max
    if isinstance(data, str):
        return len(data) < 100_000
    return False 