
import customtkinter as ctk

class SubjectSelector(ctk.CTkOptionMenu):
    def __init__(self, master, command=None, **kwargs):
        values = ["Science", "Math", "English", "Computer Science", "Social Studies", "Nepali", "Health & Population", "Accountancy", "Economics"]
        super().__init__(master, values=values, command=command, **kwargs)
        self.set("Science") # Default
