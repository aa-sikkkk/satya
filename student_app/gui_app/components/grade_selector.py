
import customtkinter as ctk

class GradeSelector(ctk.CTkOptionMenu):
    def __init__(self, master, command=None, **kwargs):
        values = ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
        super().__init__(master, values=values, command=command, **kwargs)
        self.set("Grade 10") # Default
