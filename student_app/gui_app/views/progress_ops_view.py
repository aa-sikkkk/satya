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

import customtkinter as ctk

class ProgressOpsView(ctk.CTkFrame):
    def __init__(self, master, on_export, on_import, on_reset, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_export = on_export
        self.on_import = on_import
        self.on_reset = on_reset
        self.on_back = on_back

        self.COLOR_PRIMARY = "#1A237E"    # Deep Indigo
        self.COLOR_ACCENT = "#283593"     # Lighter Indigo
        self.COLOR_SUCCESS = "#2E7D32"    # Emerald Green
        self.COLOR_WARNING = "#C62828"    # Deep Red
        self.COLOR_NEUTRAL = "#424242"    # Dark Grey
        self.COLOR_BG_CARD = "#FFFFFF"    # White
        self.COLOR_TEXT_LIGHT = "#757575" # Light Grey Text

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill='x', padx=40, pady=(30, 20))
        
        ctk.CTkLabel(
            header_frame, 
            text="Data Management 💾", 
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.COLOR_PRIMARY
        ).pack(anchor='w')
        
        ctk.CTkLabel(
            header_frame, 
            text="Backup your learning journey or start fresh.", 
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.COLOR_TEXT_LIGHT
        ).pack(anchor='w', pady=(2, 0))

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill='both', expand=True, padx=40, pady=20)

        self._create_action_card(
            self.content_frame,
            icon="📤",
            title="Backup Progress",
            desc="Save your stats and mastery to a JSON file.",
            btn_text="Export Data",
            btn_color=self.COLOR_PRIMARY,
            command=self.on_export
        )

        self._create_action_card(
            self.content_frame,
            icon="📥",
            title="Restore Progress",
            desc="Load your stats from a previous backup.",
            btn_text="Import Data",
            btn_color=self.COLOR_ACCENT,
            command=self.on_import
        )

        self._create_action_card(
            self.content_frame,
            icon="🗑️",
            title="Clear All Data",
            desc="Permanently delete all progress and start over.",
            btn_text="Reset Progress",
            btn_color=self.COLOR_WARNING,
            command=self.on_reset,
            hover_color="#B71C1C"
        )

        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill='x', padx=40, pady=30, side='bottom')
        
        self.back_btn = ctk.CTkButton(
            footer_frame, 
            text="← Back to Menu", 
            command=self.on_back,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=45,
            fg_color="transparent",
            border_width=1,
            border_color="#BDBDBD",
            text_color="#616161",
            hover_color="#F5F5F5"
        )
        self.back_btn.pack(side='left')

    def _create_action_card(self, parent, icon, title, desc, btn_text, btn_color, command, hover_color=None):
        card = ctk.CTkFrame(parent, fg_color=self.COLOR_BG_CARD, corner_radius=15, border_width=1, border_color="#E0E0E0")
        card.pack(fill='x', pady=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill='both', expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=32)).pack(side='left', padx=(0, 20))
        
        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side='left', fill='both', expand=True)
        
        ctk.CTkLabel(
            text_frame, 
            text=title, 
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#212121"
        ).pack(anchor='w')
        
        ctk.CTkLabel(
            text_frame, 
            text=desc, 
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.COLOR_TEXT_LIGHT
        ).pack(anchor='w')
        
        ctk.CTkButton(
            inner,
            text=btn_text,
            command=command,
            fg_color=btn_color,
            hover_color=hover_color if hover_color else btn_color,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=40,
            width=150
        ).pack(side='right') 