# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Rendering logic for ASCII diagrams
Handles the actual drawing of flowcharts, structures, and cycles.
"""

from typing import List, Tuple

class DiagramRenderer:
    """Handles the ASCII generation of diagrams with precise alignment."""
    
    @staticmethod
    def render_step_based_flowchart(steps: List[str]) -> str:
        """Generate a vertical step-based flowchart with arrow connectors."""
        if not steps:
            return DiagramRenderer.render_minimal_flowchart()
        
        box_width, content_width = DiagramRenderer._calculate_box_dimensions(steps)
        center = box_width // 2
        
        lines = []
        
        # 1. Start Box
        lines.extend(DiagramRenderer._draw_box("START", box_width))
        lines.append(" " * center + "│")
        lines.append(" " * center + "▼")
        
        # 2. Step Boxes
        for i, step in enumerate(steps):
            clean_step = DiagramRenderer._truncate_at_word_boundary(step.strip().upper(), content_width)
            lines.extend(DiagramRenderer._draw_box(clean_step, box_width))
            
            # Connector arrow (except after last step)
            if i < len(steps) - 1:
                lines.append(" " * center + "│")
                lines.append(" " * center + "▼")
        
        # 3. End Box
        lines.append(" " * center + "│")
        lines.append(" " * center + "▼")
        lines.extend(DiagramRenderer._draw_box("END", box_width))
        
        return "\n".join(lines)

    @staticmethod
    def render_cycle_diagram(steps: List[str]) -> str:
        """Generate a cycle diagram with a return loop."""
        if not steps: return ""
        
        box_width, content_width = DiagramRenderer._calculate_box_dimensions(steps)
        center = box_width // 2
        lines = []
        
        # Draw steps
        for i, step in enumerate(steps):
            clean_step = DiagramRenderer._truncate_at_word_boundary(step.strip().upper(), content_width)
            lines.extend(DiagramRenderer._draw_box(clean_step, box_width))
            lines.append(" " * center + "│")
            lines.append(" " * center + "▼")
        
        # The Loop Back Graphic - Mathematically aligned for CTk monospaced fonts
        padding = " " * (box_width + 2)
        lines.append(" " * center + "└" + "─" * 5 + "┐")
        lines.append(padding + "│")
        lines.append(" ┌" + "─" * (center + 4) + "─" * (box_width // 2) + "┘")
        lines.append(" ▼")
        lines.append("(CYCLE REPEATS)")
        
        return "\n".join(lines)

    @staticmethod
    def render_decision_flowchart(condition_text: str, path_a: str = "YES", path_b: str = "NO") -> str:
        """Generate a binary decision flowchart."""
        cond = DiagramRenderer._truncate_at_word_boundary(condition_text.upper(), 20)
        width = max(len(cond) + 6, 20)
        center = width // 2
        
        lines = []
        lines.extend(DiagramRenderer._draw_box("START", width))
        lines.append(" " * center + "│")
        
        # Decision Diamond Simulation
        lines.append(" " * (center - 2) + "/   \\")
        lines.append(f"<{cond.center(width)}>".center(width + 10))
        lines.append(" " * (center - 2) + "\\   /")
        
        # Branching line
        bar_half = width // 4
        lines.append(" " * (center - bar_half) + "┌" + "─" * (bar_half-1) + "┴" + "─" * (bar_half-1) + "┐")
        lines.append(" " * (center - bar_half) + "│" + " " * (bar_half*2 - 3) + "│")
        lines.append(" " * (center - bar_half) + "▼" + f" {path_a} ".center(bar_half*2 - 3) + "▼ " + path_b)
        
        return "\n".join(lines)

    @staticmethod
    def render_component_structure(components: List[str]) -> str:
        """Generate a hierarchical tree structure."""
        if not components:
            return DiagramRenderer.render_minimal_structure()
            
        width, _ = DiagramRenderer._calculate_box_dimensions(components)
        center = width // 2
        
        lines = []
        # Main Component (Root)
        lines.extend(DiagramRenderer._draw_box(components[0].upper(), width))
        
        if len(components) > 1:
            lines.append(" " * center + "│")
            lines.append(" " * (center - 1) + "[V]") # Standardized ASCII Arrow instead of CJK
            
            # Children
            for child in components[1:]:
                clean_child = DiagramRenderer._truncate_at_word_boundary(child.strip(), width-4)
                lines.append(" " * (center - 1) + "├─ " + clean_child)
                
        return "\n".join(lines)

    # Private Helpers 

    @staticmethod
    def _draw_box(text: str, width: int) -> List[str]:
        """Helper to draw a perfectly aligned ASCII box."""
        if width % 2 != 0: width += 1
        inner_width = width - 2
        padded_text = text.center(inner_width)
        return [
            "┌" + "─" * inner_width + "┐",
            "│" + padded_text + "│",
            "└" + "─" * inner_width + "┘"
        ]

    @staticmethod
    def _calculate_box_dimensions(steps: List[str]) -> Tuple[int, int]:
        if not steps: return 16, 14
        max_len = max(len(s) for s in steps)
        content_width = max(12, min(max_len, 38))
        box_width = content_width + 4
        return box_width, content_width

    @staticmethod
    def _truncate_at_word_boundary(text: str, max_length: int) -> str:
        if len(text) <= max_length: return text
        words = text.split()
        res = ""
        for w in words:
            if len(res) + len(w) + 1 <= max_length - 3:
                res += " " + w
            else:
                return res.strip() + "..."
        return res.strip()

    @staticmethod
    def render_minimal_flowchart() -> str:
        return "┌──────┐\n│ START│\n└──┬───┘\n   ▼\n┌──────┐\n│ END  │\n└──────┘"

    @staticmethod
    def render_minimal_structure() -> str:
        return "┌──────────┐\n│ COMPONENT│\n└──────────┘"

    @staticmethod
    def calculate_adaptive_limits(content_length: int, num_items: int) -> Tuple[int, int]:
        if content_length < 500: return min(num_items, 4), 20
        return min(num_items, 8), 15