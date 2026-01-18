"""
Startup loader for Satya GUI - Preloads all models before showing main window
"""

import customtkinter as ctk
import tkinter as tk
import threading
import time
from pathlib import Path

class StartupLoader(tk.Tk):
    """Loading screen shown during model initialization."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Loading Satya...")
        self.geometry("400x250")
        self.resizable(False, False)
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (250 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.overrideredirect(True)
        
        ctk.set_appearance_mode('light')
        ctk.set_default_color_theme('green')
        
        self.frame = ctk.CTkFrame(self, corner_radius=15)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.frame,
            text="🚀 Satya Learning System",
            font=("Arial", 20, "bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.frame,
            text="Initializing...",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self.frame, width=300)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        # Detail label
        self.detail_label = ctk.CTkLabel(
            self.frame,
            text="",
            font=("Arial", 10),
            text_color="gray"
        )
        self.detail_label.pack(pady=5)
        
    def update_status(self, status, detail="", progress=None):
        """Update loading status."""
        self.status_label.configure(text=status)
        self.detail_label.configure(text=detail)
        if progress is not None:
            self.progress.set(progress)
        self.update()
        self.update_idletasks()
