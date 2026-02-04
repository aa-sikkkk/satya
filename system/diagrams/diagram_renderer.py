# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
ASCII Diagram Renderer

Renders flowcharts, structures, comparisons, and cycles as ASCII art.
Used by diagram_service.py to visualize YAML-based diagram data.
"""

from typing import List, Tuple, Dict


class DiagramRenderer:
    """Generates ASCII diagrams with precise alignment."""
    
    @staticmethod
    def render_step_based_flowchart(steps: List[str]) -> str:
        """Render a vertical step-based flowchart with arrow connectors."""
        if not steps:
            return DiagramRenderer.render_minimal_flowchart()
        
        box_width, content_width = DiagramRenderer._calculate_box_dimensions(steps)
        center = box_width // 2
        
        lines = []
        
        # Start Box
        lines.extend(DiagramRenderer._draw_box("START", box_width))
        lines.append(" " * center + "│")
        lines.append(" " * center + "▼")
        
        # Step Boxes
        for i, step in enumerate(steps):
            clean_step = DiagramRenderer._truncate_at_word_boundary(step.strip().upper(), content_width)
            lines.extend(DiagramRenderer._draw_box(clean_step, box_width))
            
            if i < len(steps) - 1:
                lines.append(" " * center + "│")
                lines.append(" " * center + "▼")
        
        # End Box
        lines.append(" " * center + "│")
        lines.append(" " * center + "▼")
        lines.extend(DiagramRenderer._draw_box("END", box_width))
        
        return "\n".join(lines)

    @staticmethod
    def render_cycle_diagram(steps: List[str]) -> str:
        """Render a cycle diagram with a return loop."""
        if not steps:
            return ""
        
        box_width, content_width = DiagramRenderer._calculate_box_dimensions(steps)
        center = box_width // 2
        lines = []
        
        for i, step in enumerate(steps):
            clean_step = DiagramRenderer._truncate_at_word_boundary(step.strip().upper(), content_width)
            lines.extend(DiagramRenderer._draw_box(clean_step, box_width))
            lines.append(" " * center + "│")
            lines.append(" " * center + "▼")
        
        # Loop back graphic
        padding = " " * (box_width + 2)
        lines.append(" " * center + "└" + "─" * 5 + "┐")
        lines.append(padding + "│")
        lines.append(" ┌" + "─" * (center + 4) + "─" * (box_width // 2) + "┘")
        lines.append(" ▼")
        lines.append("(CYCLE REPEATS)")
        
        return "\n".join(lines)

    @staticmethod
    def render_decision_flowchart(condition_text: str, path_a: str = "YES", path_b: str = "NO") -> str:
        """Render a binary decision flowchart."""
        cond = DiagramRenderer._truncate_at_word_boundary(condition_text.upper(), 20)
        width = max(len(cond) + 6, 20)
        center = width // 2
        
        lines = []
        lines.extend(DiagramRenderer._draw_box("START", width))
        lines.append(" " * center + "│")
        
        # Decision diamond
        lines.append(" " * (center - 2) + "/   \\")
        lines.append(f"<{cond.center(width)}>".center(width + 10))
        lines.append(" " * (center - 2) + "\\   /")
        
        bar_half = width // 4
        lines.append(" " * (center - bar_half) + "┌" + "─" * (bar_half-1) + "┴" + "─" * (bar_half-1) + "┐")
        lines.append(" " * (center - bar_half) + "│" + " " * (bar_half*2 - 3) + "│")
        lines.append(" " * (center - bar_half) + "▼" + f" {path_a} ".center(bar_half*2 - 3) + "▼ " + path_b)
        
        return "\n".join(lines)

    @staticmethod
    def render_component_structure(components: List[str]) -> str:
        """Render a hierarchical tree structure."""
        if not components:
            return DiagramRenderer.render_minimal_structure()
            
        width, _ = DiagramRenderer._calculate_box_dimensions(components)
        center = width // 2
        
        lines = []
        # Root component
        lines.extend(DiagramRenderer._draw_box(components[0].upper(), width))
        
        if len(components) > 1:
            lines.append(" " * center + "│")
            lines.append(" " * (center - 1) + "[V]")
            
            # Children
            for child in components[1:]:
                clean_child = DiagramRenderer._truncate_at_word_boundary(child.strip(), width-4)
                lines.append(" " * (center - 1) + "├─ " + clean_child)
                
        return "\n".join(lines)

    @staticmethod
    def render_comparison_table(data: Dict) -> str:
        """Render a comparison table showing similarities and differences."""
        similarities = data.get('similarities', [])
        differences = data.get('differences', [])
        
        # Handle dict differences (item_a vs item_b format)
        if isinstance(differences, dict):
            diff_list = []
            for key, val in differences.items():
                if isinstance(val, dict):
                    diff_list.append(f"{key}: {val.get('item_a', '')} vs {val.get('item_b', '')}")
                else:
                    diff_list.append(f"{key}: {val}")
            differences = diff_list
        
        lines = []
        
        lines.append("┌" + "─" * 50 + "┐")
        lines.append("│" + " COMPARISON TABLE ".center(50) + "│")
        lines.append("├" + "─" * 50 + "┤")
        
        if similarities:
            lines.append("│" + " SIMILARITIES:".ljust(50) + "│")
            for sim in similarities[:4]:
                sim_text = sim[:45] + "..." if len(sim) > 45 else sim
                lines.append("│  • " + sim_text.ljust(46) + "│")
            lines.append("│" + " " * 50 + "│")
        
        if similarities and differences:
            lines.append("├" + "─" * 50 + "┤")
        
        if differences:
            lines.append("│" + " DIFFERENCES:".ljust(50) + "│")
            for diff in differences[:4]:
                diff_text = str(diff)[:45] + "..." if len(str(diff)) > 45 else str(diff)
                lines.append("│  • " + diff_text.ljust(46) + "│")
            lines.append("│" + " " * 50 + "│")
        
        lines.append("└" + "─" * 50 + "┘")
        
        return "\n".join(lines)

    @staticmethod
    def render_for_concept(concept_data: Dict) -> str:
        """Route to appropriate renderer based on concept type."""
        concept_type = concept_data.get('concept_type', '').upper()
        visual_data = concept_data.get('visual_data', {})
        
        if concept_type == 'PROCESS':
            steps = visual_data.get('steps', [])
            if steps:
                return DiagramRenderer.render_step_based_flowchart(steps)
                
        elif concept_type == 'COMPARISON':
            return DiagramRenderer.render_comparison_table(visual_data)
            
        elif concept_type in ('HIERARCHY', 'STRUCTURE'):
            components = visual_data.get('components', [])
            if components:
                return DiagramRenderer.render_component_structure(components)
        
        return DiagramRenderer.render_minimal_flowchart()

    @staticmethod
    def _draw_box(text: str, width: int) -> List[str]:
        """Draw a perfectly aligned ASCII box."""
        if width % 2 != 0:
            width += 1
        inner_width = width - 2
        padded_text = text.center(inner_width)
        return [
            "┌" + "─" * inner_width + "┐",
            "│" + padded_text + "│",
            "└" + "─" * inner_width + "┘"
        ]

    @staticmethod
    def _calculate_box_dimensions(steps: List[str]) -> Tuple[int, int]:
        if not steps:
            return 16, 14
        max_len = max(len(s) for s in steps)
        content_width = max(12, min(max_len, 38))
        box_width = content_width + 4
        return box_width, content_width

    @staticmethod
    def _truncate_at_word_boundary(text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
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