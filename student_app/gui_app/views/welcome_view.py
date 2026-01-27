# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Modern Welcome View for Satya Learning System

Provides an aesthetic and responsive welcome screen with smooth animations.
"""

import customtkinter as ctk
import re
import threading


class WelcomeView(ctk.CTkFrame):
    """
    Beautiful welcome screen with modern design and smooth user experience.
    """
    
    def __init__(self, master, on_login, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_login = on_login
        self._processing = False
        
        # Configure grid for centering
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main container for centered content
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Content frame with padding
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="")
        
        self._create_welcome_ui()
        
    def _create_welcome_ui(self):
        """Create the welcome UI elements with modern design."""
        
        # Title with gradient effect (using emoji and styling)
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="🌟 Satya Learning System",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color="#2E7D32"
        )
        self.title_label.pack()
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.content_frame,
            text="Your AI-Powered Learning Companion",
            font=ctk.CTkFont(size=18),
            text_color="#666666"
        )
        self.subtitle_label.pack(pady=(0, 40))
        
        # Features preview
        features_frame = ctk.CTkFrame(self.content_frame, fg_color="#F5F5F5", corner_radius=15)
        features_frame.pack(pady=(0, 40), padx=40, fill="x")
        
        features_text = """
        ✨ Interactive Learning  •  🤖 AI-Powered Answers  •  📊 Progress Tracking
        """
        ctk.CTkLabel(
            features_frame,
            text=features_text,
            font=ctk.CTkFont(size=14),
            text_color="#424242",
            justify="center"
        ).pack(pady=15, padx=20)
        
        # Login section
        login_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        login_frame.pack(pady=(0, 20))
        
        # Username label
        username_label = ctk.CTkLabel(
            login_frame,
            text="Enter your username to begin:",
            font=ctk.CTkFont(size=16, weight="normal"),
            text_color="#424242"
        )
        username_label.pack(pady=(0, 10))
        
        # Username entry with better styling
        self.username_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Type your username here...",
            width=320,
            height=45,
            font=ctk.CTkFont(size=16),
            corner_radius=10,
            border_width=2,
            border_color="#BDBDBD"
        )
        self.username_entry.pack(pady=10)
        self.username_entry.bind('<Return>', lambda e: self.try_login())
        self.username_entry.bind('<KeyRelease>', self._on_entry_change)
        
        # Error label with better styling
        self.error_label = ctk.CTkLabel(
            login_frame,
            text="",
            text_color="#E53935",
            font=ctk.CTkFont(size=13),
            height=20
        )
        self.error_label.pack(pady=(5, 0))
        
        # Login button with modern design
        self.login_btn = ctk.CTkButton(
            login_frame,
            text="🚀 Start Learning Journey",
            command=self.try_login,
            width=320,
            height=50,
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=12,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            state="normal"
        )
        self.login_btn.pack(pady=(15, 0))
        
        # Help text
        help_text = ctk.CTkLabel(
            self.content_frame,
            text="Username: 3-32 characters (letters, numbers, underscores)",
            font=ctk.CTkFont(size=12),
            text_color="#9E9E9E"
        )
        help_text.pack(pady=(20, 0))
        
        # Focus on entry
        self.after(100, lambda: self.username_entry.focus())
    
    def _on_entry_change(self, event=None):
        """Handle entry changes to provide real-time feedback."""
        if self._processing:
            return
        
        username = self.username_entry.get().strip()
        if username:
            if re.match(r"^[A-Za-z0-9_]{3,32}$", username):
                self.error_label.configure(text="")
                self.login_btn.configure(state="normal")
            else:
                if len(username) < 3:
                    self.error_label.configure(text="Username must be at least 3 characters")
                elif len(username) > 32:
                    self.error_label.configure(text="Username must be 32 characters or less")
                else:
                    self.error_label.configure(text="Only letters, numbers, and underscores allowed")
                self.login_btn.configure(state="normal")
        else:
            self.error_label.configure(text="")
            self.login_btn.configure(state="normal")
    
    def try_login(self):
        """Handle login attempt with validation and feedback."""
        if self._processing:
            return
        
        username = self.username_entry.get().strip()
        
        if not username:
            self.error_label.configure(text="Please enter a username")
            return
        
        if not re.match(r"^[A-Za-z0-9_]{3,32}$", username):
            self.error_label.configure(text="Invalid username. Use 3-32 letters, numbers, or underscores.")
            return
        
        # Disable UI during processing
        self._processing = True
        self.error_label.configure(text="")
        self.username_entry.configure(state="disabled")
        self.login_btn.configure(
            text="Loading...",
            state="disabled",
            fg_color="#9E9E9E"
        )
        
        # Process login in a separate thread to keep UI responsive
        def process_login():
            try:
                # Small delay for smooth transition
                import time
                time.sleep(0.2)
                
                # Call login callback on main thread
                self.after(0, lambda: self._complete_login(username))
            except Exception as e:
                self.after(0, lambda: self._login_error(str(e)))
        
        threading.Thread(target=process_login, daemon=True).start()
    
    def _complete_login(self, username):
        """Complete the login process."""
        self._processing = False
        self.on_login(username)
    
    def _login_error(self, error_msg):
        """Handle login error."""
        self._processing = False
        self.username_entry.configure(state="normal")
        self.login_btn.configure(
            text="🚀 Start Learning Journey",
            state="normal",
            fg_color="#2E7D32"
        )
        self.error_label.configure(text=f"Error: {error_msg}") 