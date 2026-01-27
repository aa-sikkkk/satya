# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

import customtkinter as ctk

class DiagramViewer(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.label = ctk.CTkLabel(self, text="ASCII Diagram Viewer", font=("Consolas", 12))
        self.label.pack(pady=10)
        
        self.text_area = ctk.CTkTextbox(self, font=("Consolas", 10))
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        
    def display(self, ascii_art: str):
        self.text_area.delete("0.0", "end")
        self.text_area.insert("0.0", ascii_art)
