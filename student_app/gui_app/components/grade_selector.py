# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

import customtkinter as ctk

class GradeSelector(ctk.CTkOptionMenu):
    def __init__(self, master, command=None, **kwargs):
        values = ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
        super().__init__(master, values=values, command=command, **kwargs)
        self.set("Grade 10") # Default
