# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Enhanced DiagramViewer Component

Displays ASCII diagrams with concept-aware styling.
Supports PROCESS (flowcharts), COMPARISON (tables), and HIERARCHY (trees).
"""

import customtkinter as ctk
from typing import Optional


# =============================================================================
# CONCEPT-AWARE COLOR SCHEMES
# =============================================================================

DIAGRAM_STYLES = {
    # PROCESS diagrams: Orange/amber tones (sequential flow)
    'process': {
        'bg_color': '#fff3e0',
        'header_color': '#e65100',
        'icon': '📊',
        'label': 'Process Flow'
    },
    # COMPARISON diagrams: Blue/teal tones (analysis)
    'comparison': {
        'bg_color': '#e0f7fa',
        'header_color': '#00838f',
        'icon': '⚖️',
        'label': 'Comparison Table'
    },
    # HIERARCHY diagrams: Green tones (structure)
    'hierarchy': {
        'bg_color': '#e8f5e9',
        'header_color': '#2e7d32',
        'icon': '🌳',
        'label': 'Structure Diagram'
    },
    # CYCLE diagrams: Purple tones (repeating)
    'cycle': {
        'bg_color': '#f3e5f5',
        'header_color': '#7b1fa2',
        'icon': '🔄',
        'label': 'Cycle Diagram'
    },
    # Default/fallback styling
    'default': {
        'bg_color': '#fafafa',
        'header_color': '#424242',
        'icon': '📈',
        'label': 'Visual Representation'
    }
}


class DiagramViewer(ctk.CTkFrame):
    """
    Enhanced ASCII diagram viewer with concept-aware styling.
    
    Features:
    - Dynamic styling based on diagram type (PROCESS, COMPARISON, etc.)
    - Monospace font for proper ASCII alignment
    - Auto-height calculation based on content
    - Horizontal scrolling for wide diagrams
    """
    
    def __init__(self, master, diagram_type: str = 'default', **kwargs):
        """
        Initialize the diagram viewer.
        
        Args:
            master: Parent widget
            diagram_type: One of 'process', 'comparison', 'hierarchy', 'cycle', 'default'
        """
        # Get style for this diagram type
        self.diagram_type = diagram_type.lower() if diagram_type else 'default'
        self.style = DIAGRAM_STYLES.get(self.diagram_type, DIAGRAM_STYLES['default'])
        
        # Apply background color
        kwargs.setdefault('fg_color', self.style['bg_color'])
        kwargs.setdefault('corner_radius', 8)
        
        super().__init__(master, **kwargs)
        
        # Header with icon and label
        self.header = ctk.CTkLabel(
            self, 
            text=f"{self.style['icon']} {self.style['label']}", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.style['header_color']
        )
        self.header.pack(pady=(10, 5), padx=10, anchor='w')
        
        # Monospace text area for ASCII diagrams
        self.text_area = ctk.CTkTextbox(
            self, 
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap='none',  # Preserve ASCII alignment
            height=250,   # Default height, can be adjusted
            fg_color='#ffffff'  # White background for readability
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def display(self, ascii_art: str, auto_height: bool = True):
        """
        Display ASCII diagram content.
        
        Args:
            ascii_art: The ASCII diagram text
            auto_height: Whether to auto-calculate height based on content
        """
        self.text_area.configure(state="normal")
        self.text_area.delete("0.0", "end")
        self.text_area.insert("0.0", ascii_art)
        self.text_area.configure(state="disabled")
        
        if auto_height:
            self._adjust_height(ascii_art)
    
    def _adjust_height(self, text: str):
        """
        Calculate and set optimal height for the content.
        
        Args:
            text: The ASCII diagram text
        """
        if not text:
            return
            
        # Count lines and calculate height
        line_count = text.count('\n') + 1
        line_height = 20  # Approximate pixels per line
        padding = 30
        
        calculated_height = (line_count * line_height) + padding
        
        # Clamp to reasonable bounds
        final_height = max(120, min(calculated_height, 500))
        self.text_area.configure(height=final_height)
    
    def set_diagram_type(self, diagram_type: str):
        """
        Update styling based on diagram type.
        
        Args:
            diagram_type: One of 'process', 'comparison', 'hierarchy', 'cycle'
        """
        self.diagram_type = diagram_type.lower() if diagram_type else 'default'
        self.style = DIAGRAM_STYLES.get(self.diagram_type, DIAGRAM_STYLES['default'])
        
        # Update styling
        self.configure(fg_color=self.style['bg_color'])
        self.header.configure(
            text=f"{self.style['icon']} {self.style['label']}",
            text_color=self.style['header_color']
        )


def get_diagram_style(diagram_type: str) -> dict:
    """
    Get the style dictionary for a diagram type.
    
    Args:
        diagram_type: Type of diagram
        
    Returns:
        Style dictionary with bg_color, header_color, icon, label
    """
    dtype = diagram_type.lower() if diagram_type else 'default'
    return DIAGRAM_STYLES.get(dtype, DIAGRAM_STYLES['default'])
