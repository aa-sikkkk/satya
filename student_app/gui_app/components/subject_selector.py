
import customtkinter as ctk

class SubjectSelector(ctk.CTkOptionMenu):
    def __init__(self, master, command=None, **kwargs):
        values = ["Science", "Math", "English Grammar", "Computer Science", "Social Studies"]
        super().__init__(master, values=values, command=command, **kwargs)
        self.set("Science") # Default
