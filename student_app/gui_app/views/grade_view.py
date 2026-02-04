# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

import customtkinter as ctk


class GradeView(ctk.CTkFrame):
    """
    Grade selection screen matching SubjectView design pattern.
    
    Displays grades 8-12 as a 2-column grid of buttons.
    """
    
    def __init__(self, master, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.grades = [8, 9, 10, 11, 12]

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(40, 30))
        
        self.label = ctk.CTkLabel(
            self.header_frame, 
            text="Select Your Grade", 
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        )
        self.label.pack()
        
        ctk.CTkLabel(
            self.header_frame,
            text="Choose your current class level",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="gray70"
        ).pack(pady=(5, 0))

        # 2-column grid of grade buttons
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self, width=650, height=300, fg_color="transparent"
        )
        self.scrollable_frame.pack(pady=(0, 20), padx=20, fill='both', expand=True)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        self.grade_buttons = []
        for i, grade in enumerate(self.grades):
            btn = ctk.CTkButton(
                self.scrollable_frame, 
                text=f"Grade {grade}", 
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                height=60,
                corner_radius=12,
                fg_color="#3949AB",  # Indigo 600 (same as SubjectView)
                hover_color="#303F9F",  # Indigo 700
                command=lambda g=grade: self.on_select(g)
            )
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
            self.grade_buttons.append(btn)

        # Back button
        self.back_btn = ctk.CTkButton(
            self, 
            text="Back to Main Menu", 
            command=self.on_back, 
            fg_color="transparent", 
            border_width=1, 
            border_color="#bdbdbd",
            text_color=("gray10", "#bdbdbd"),
            hover_color=("gray90", "gray20")
        )
        self.back_btn.pack(pady=(10, 30))
