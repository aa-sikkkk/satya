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

