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

class QuestionView(ctk.CTkFrame):
    def __init__(self, master, question, on_submit, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_submit = on_submit
        self.on_back = on_back
        self.question = question

        # Header Area
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(40, 30))
        
        self.label = ctk.CTkLabel(
            self.header_frame, 
            text="Quiz Time!", 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
        )
        self.label.pack()
        
        ctk.CTkLabel(
            self.header_frame,
            text="Test your knowledge",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="gray70"
        ).pack(pady=(5, 0))

        # Question Content
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=200)
        self.content_frame.pack(pady=(0, 20), padx=40, fill='both', expand=True)

        self.q_text = ctk.CTkLabel(
            self.content_frame, 
            text=question, 
            font=ctk.CTkFont(family="Segoe UI", size=20), 
            wraplength=650, 
            justify='left'
        )
        self.q_text.pack(pady=20)

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(pady=10, fill='x', padx=40)

        self.answer_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Type your answer here...", 
            height=50,
            font=ctk.CTkFont(family="Segoe UI", size=16)
        )
        self.answer_entry.pack(fill='x', pady=(0, 20))
        self.answer_entry.bind('<Return>', lambda e: self.submit())

        # Footer Actions
        self.submit_btn = ctk.CTkButton(
            self, 
            text="Submit Answer", 
            command=self.submit,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=50,
            width=200,
            corner_radius=25,
            fg_color="#43A047", # Green 600
            hover_color="#2E7D32" # Green 800
        )
        self.submit_btn.pack(side="bottom", pady=(10, 30))
        
        self.back_btn = ctk.CTkButton(
            self, 
            text="Cancel Quiz", 
            command=self.on_back, 
            fg_color="transparent", 
            border_width=1, 
            border_color="#bdbdbd",
            text_color=("gray10", "#bdbdbd"),
            hover_color=("gray90", "gray20")
        )
        self.back_btn.pack(side="bottom", pady=(0, 10))

    def submit(self):
        answer = self.answer_entry.get().strip()
        if not answer:
            return
        self.on_submit(answer)

    def _clear_input_area(self):
        self.answer_entry.pack_forget()
        self.submit_btn.pack_forget()
        self.input_frame.pack_forget()
        self.back_btn.pack_forget()

    def show_correct(self, feedback: str):
        self._clear_input_area()
        
        # Status
        status_label = ctk.CTkLabel(
            self, 
            text="✅ Correct!", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#43A047"
        )
        status_label.pack(pady=(10, 20))
        
        # Feedback Card
        self._show_feedback_card(feedback)
        
        # Next Button
        self.next_btn = ctk.CTkButton(
            self,
            text="Next Question",
            command=lambda: self.on_back(), # Currently loops back to logic in main window
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=50,
            width=200,
            corner_radius=25,
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        self.next_btn.pack(side="bottom", pady=40)

    def show_incorrect(self, feedback: str):
        self._clear_input_area()
        
        # Status
        status_label = ctk.CTkLabel(
            self, 
            text="❌ Incorrect", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#E53935"
        )
        status_label.pack(pady=(10, 20))
        
        # Feedback Card
        self._show_feedback_card(feedback)
        
        # Next Button
        self.next_btn = ctk.CTkButton(
            self,
            text="Next Question",
            command=lambda: self.on_back(),
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=50,
            width=200,
            corner_radius=25,
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        self.next_btn.pack(side="bottom", pady=40)

    def _show_feedback_card(self, text):
        container = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=15)
        container.pack(fill='x', padx=40, pady=10)
        
        title = ctk.CTkLabel(
            container, 
            text="Feedback:", 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w"
        )
        title.pack(fill='x', padx=20, pady=(15, 5))
        
        content = ctk.CTkLabel(
            container, 
            text=text, 
            font=ctk.CTkFont(family="Segoe UI", size=16),
            justify="left",
            wraplength=600,
            anchor="w"
        )
        content.pack(fill='x', padx=20, pady=(0, 20))