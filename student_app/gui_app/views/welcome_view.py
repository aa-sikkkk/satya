import customtkinter as ctk
import re

class WelcomeView(ctk.CTkFrame):
    def __init__(self, master, on_login, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_login = on_login
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Welcome to NEBedu!", font=ctk.CTkFont(size=28, weight="bold"))
        self.label.pack(pady=(60, 10))
        self.desc = ctk.CTkLabel(self, text="Please enter your username to begin:", font=ctk.CTkFont(size=16))
        self.desc.pack(pady=(0, 20))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=220, font=ctk.CTkFont(size=16))
        self.username_entry.pack(pady=10)
        self.username_entry.bind('<Return>', lambda e: self.try_login())

        self.error_label = ctk.CTkLabel(self, text="", text_color="red", font=ctk.CTkFont(size=14))
        self.error_label.pack(pady=(5, 0))

        self.login_btn = ctk.CTkButton(self, text="Start Learning", command=self.try_login)
        self.login_btn.pack(pady=30)

    def try_login(self):
        username = self.username_entry.get().strip()
        if re.match(r"^[A-Za-z0-9_]{3,32}$", username):
            self.error_label.configure(text="")
            self.on_login(username)
        else:
            self.error_label.configure(text="Invalid username. Use 3-32 letters, numbers, or underscores.") 