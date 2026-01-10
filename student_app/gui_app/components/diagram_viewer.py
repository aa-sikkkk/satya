
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
