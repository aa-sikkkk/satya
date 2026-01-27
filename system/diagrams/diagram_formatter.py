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
Utilities for formatting and trimming diagram output
Focuses on preserving ASCII integrity for CustomTkinter display.
"""

from typing import Optional

DEFAULT_MAX_WIDTH = 100
MIN_WIDTH = 40
MAX_WIDTH = 80 
TRUNCATION_SUFFIX = "..."


class DiagramFormatter:
    """Handles formatting and structural cleaning for ASCII diagrams."""
    
    @staticmethod
    def format(diagram: str) -> str:
        """
        Cleans the diagram by removing LLM chatter and fixing indentation.
        """
        if not diagram:
            return ""
        
        lines = [line.rstrip() for line in diagram.split('\n')]

        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop(-1)
            
        if not lines:
            return ""

        non_empty_lines = [l for l in lines if l.strip()]
        if non_empty_lines:
            min_indent = min(len(l) - len(l.lstrip()) for l in non_empty_lines)
            lines = [l[min_indent:] if len(l) >= min_indent else l for l in lines]
        
        return '\n'.join(lines)
    
    @staticmethod
    def trim(diagram: str, max_width: Optional[int] = None) -> str:
        """
        Safety trimmer. Unlike a standard text trimmer, this ensures we don't 
        accidentally slice off the right side of an ASCII box if we can help it.
        """
        if not diagram:
            return ""
        
        lines = diagram.split('\n')
        actual_max = max_width or MAX_WIDTH
        
        trimmed = []
        for line in lines:
            if len(line) > actual_max:
                if any(c in line for c in "┌┐└┘│├┤"):
                    # For ASCII boxes, truncation usually ruins the visual.
                    # We truncate but try to keep the string length consistent.
                    trimmed.append(line[:actual_max-3] + "...")
                else:
                    trimmed.append(line[:actual_max-3] + "...")
            else:
                trimmed.append(line)
        
        return '\n'.join(trimmed)

    @staticmethod
    def _calculate_adaptive_width(lines: list[str]) -> int:
        """Helper to find the best viewing width."""
        if not lines:
            return DEFAULT_MAX_WIDTH
        
        lengths = [len(l) for l in lines if l.strip()]
        if not lengths: return DEFAULT_MAX_WIDTH
        
        avg_length = sum(lengths) / len(lengths)
        return max(MIN_WIDTH, min(MAX_WIDTH, int(avg_length + 10)))


def format_diagram(diagram: str) -> str:
    return DiagramFormatter.format(diagram)


def trim_diagram(diagram: str, max_width: Optional[int] = None) -> str:
    return DiagramFormatter.trim(diagram, max_width)