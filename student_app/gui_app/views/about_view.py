# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

import customtkinter as ctk

class AboutView(ctk.CTkFrame):
    def __init__(self, master, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_back = on_back

        self.label = ctk.CTkLabel(self, text="About Satya", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        about_text = """
        Welcome to Satya, your personal AI-powered learning companion!

        Satya is designed to help you master new concepts and track your progress in a fun and interactive way. Whether you're exploring new subjects or preparing for exams, Satya is here to support your learning journey.

        Key Features:
        - Browse Subjects: Dive into a wide range of subjects and topics, each with detailed concepts and learning materials.
        - Interactive Q&A: Test your knowledge with interactive questions and get instant feedback.
        - Ask AI: Have a question? Ask our AI assistant and get detailed answers, powered by advanced language models.
        - Progress Tracking: Monitor your progress, identify your strengths and weaknesses, and get recommendations on what to study next.
        - Offline First: Satya is designed to work offline, so you can learn anytime, anywhere.

        We hope you enjoy your learning experience with Satya!
        """

        self.textbox = ctk.CTkTextbox(self, width=600, height=300, font=ctk.CTkFont(size=16), wrap='word')
        self.textbox.insert('1.0', about_text)
        self.textbox.configure(state="disabled")
        self.textbox.pack(pady=10, padx=20, fill="both", expand=True)

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back)
        self.back_btn.pack(pady=20)
