# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
System utilities package.

Provides utility functions for resource path resolution and other system operations.
"""

from .resource_path import (
    get_base_path,
    resolve_content_dir,
    resolve_model_dir,
    resolve_chroma_db_dir
)

__all__ = [
    'get_base_path',
    'resolve_content_dir',
    'resolve_model_dir',
    'resolve_chroma_db_dir',
]

