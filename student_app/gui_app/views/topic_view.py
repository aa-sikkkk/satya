# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

import customtkinter as ctk

class TopicView(ctk.CTkFrame):
    def __init__(self, master, topics, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.topics = topics

        # Main Title Area
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(40, 25))
        
        self.label = ctk.CTkLabel(
            self.header_frame, 
            text="Select a Topic", 
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        )
        self.label.pack()
        
        ctk.CTkLabel(
            self.header_frame,
            text="Choose a chapter to continue",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="gray70"
        ).pack(pady=(5, 0))

        # Back button 
        self.back_btn = ctk.CTkButton(
            self, 
            text="Back to Subjects", 
            command=self.on_back, 
            fg_color="transparent", 
            border_width=1, 
            border_color="#bdbdbd",
            text_color=("gray10", "#bdbdbd"),
            hover_color=("gray90", "gray20")
        )
        self.back_btn.pack(side="bottom", pady=(10, 30))

        # Scrollable container
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=650, height=400, fg_color="transparent")
        self.scrollable_frame.pack(pady=(0, 20), padx=20, fill='both', expand=True)

        # 2-column Grid Layout
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        # Topic Cards
        for i, topic in enumerate(topics):
            label = topic.get("label") if isinstance(topic, dict) and "label" in topic else (topic.get("name") if isinstance(topic, dict) else topic)
            
            btn = ctk.CTkButton(
                self.scrollable_frame, 
                text=label, 
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                height=60,
                corner_radius=12,
                fg_color="#3949AB", # Indigo 600
                hover_color="#303F9F", # Indigo 700
                command=lambda t=topic: self.on_select(t)
            )
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew") 