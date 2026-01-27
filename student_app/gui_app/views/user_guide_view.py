# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import customtkinter as ctk
import os
import re

class UserGuideView(ctk.CTkFrame):
    def __init__(self, master, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_back = on_back

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill='x', pady=20, padx=20)
        
        self.title = ctk.CTkLabel(
            self.header, 
            text="📘 User Guide", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2E7D32"
        )
        self.title.pack(side='left')
        
        self.back_btn = ctk.CTkButton(
            self.header, 
            text="Back to Menu", 
            command=self.on_back,
            width=120
        )
        self.back_btn.pack(side='right')

        # Content
        self.text_area = ctk.CTkTextbox(
            self, 
            font=ctk.CTkFont(family="Segoe UI", size=14),
            wrap="word"
        )
        self.text_area.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Configure tags immediately after textbox creation
        self._configure_tags()
        
        self._load_guide_content()

    def _configure_tags(self):
        """Configure all text tags for markdown styling"""
        text_widget = self.text_area._textbox
        
        # Headers
        text_widget.tag_config("h1", font=("Segoe UI", 22, "bold"), 
                              foreground="#2E7D32", spacing3=10, spacing1=5)
        text_widget.tag_config("h2", font=("Segoe UI", 18, "bold"), 
                              foreground="#388E3C", spacing3=8, spacing1=5)
        text_widget.tag_config("h3", font=("Segoe UI", 15, "bold"), 
                              foreground="#43A047", spacing3=5, spacing1=3)
        
        # Body text
        text_widget.tag_config("body", font=("Segoe UI", 14))
        text_widget.tag_config("bold", font=("Segoe UI", 14, "bold"))
        text_widget.tag_config("italic", font=("Segoe UI", 14, "italic"))
        text_widget.tag_config("bold_italic", font=("Segoe UI", 14, "bold italic"))
        
        # Bullet points
        text_widget.tag_config("bullet", font=("Segoe UI", 14), 
                              lmargin1=30, lmargin2=50)
        text_widget.tag_config("bullet_bold", font=("Segoe UI", 14, "bold"), 
                              lmargin1=30, lmargin2=50)
        text_widget.tag_config("bullet_italic", font=("Segoe UI", 14, "italic"), 
                              lmargin1=30, lmargin2=50)
        text_widget.tag_config("bullet_bold_italic", font=("Segoe UI", 14, "bold italic"), 
                              lmargin1=30, lmargin2=50)
        
        # Code/monospace
        text_widget.tag_config("code", font=("Consolas", 13), 
                              background="#f0f0f0", foreground="#d63384")
        text_widget.tag_config("bullet_code", font=("Consolas", 13), 
                              background="#f0f0f0", foreground="#d63384",
                              lmargin1=30, lmargin2=50)
        
        # Horizontal rule
        text_widget.tag_config("hr", font=("Segoe UI", 14), 
                              foreground="#cccccc", spacing3=10, spacing1=10)

    def _load_guide_content(self):
        try:
            # Try to find USER_GUIDE.md in project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
            guide_path = os.path.join(project_root, "USER_GUIDE.md")
            
            # Fallback
            if not os.path.exists(guide_path):
                guide_path = "USER_GUIDE.md"
            
            if os.path.exists(guide_path):
                with open(guide_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Ensure textbox is editable
                self.text_area.configure(state="normal")
                self._insert_markdown(content)
                self.text_area.configure(state="disabled")
            else:
                self.text_area.configure(state="normal")
                self.text_area.insert("0.0", "Error: USER_GUIDE.md not found.")
                self.text_area.configure(state="disabled")
                
        except Exception as e:
            self.text_area.configure(state="normal")
            self.text_area.insert("0.0", f"Error loading guide: {str(e)}")
            self.text_area.configure(state="disabled")

    def _insert_markdown(self, text):
        """Parse and insert markdown-formatted text"""
        lines = text.split('\n')
        text_widget = self.text_area._textbox
        
        for line in lines:
            original_line = line
            line = line.rstrip()
            
            if not line:
                text_widget.insert("end", "\n")
                continue

            # Horizontal rule
            if line.strip() in ['---', '***', '___']:
                text_widget.insert("end", "─" * 80 + "\n", "hr")
                continue

            # Headers (check longest patterns first)
            if line.startswith('### '):
                text_widget.insert("end", line[4:] + "\n", "h3")
                continue
            elif line.startswith('## '):
                text_widget.insert("end", line[3:] + "\n", "h2")
                continue
            elif line.startswith('# '):
                text_widget.insert("end", line[2:] + "\n", "h1")
                continue
            
            # Bullet points
            if line.startswith('* ') or line.startswith('- '):
                content = line[2:]
                self._insert_inline_formatting("• " + content + "\n", 
                                              base_tag="bullet")
                continue
            
            # Numbered lists
            if re.match(r'^\d+\.\s', line):
                self._insert_inline_formatting(line + "\n", 
                                              base_tag="bullet")
                continue
            
            # Regular paragraphs
            self._insert_inline_formatting(line + "\n", base_tag="body")

    def _insert_inline_formatting(self, text, base_tag="body"):
        """
        Parse inline markdown including bold (**), italic (*), and code (`)
        Handles nested formatting properly
        """
        text_widget = self.text_area._textbox
        
        # Process the text character by character with state tracking
        i = 0
        while i < len(text):
            # Check for bold+italic (***text***)
            if text[i:i+3] == '***':
                end = text.find('***', i+3)
                if end != -1:
                    content = text[i+3:end]
                    tag = f"{base_tag}_bold_italic" if base_tag != "body" else "bold_italic"
                    text_widget.insert("end", content, tag)
                    i = end + 3
                    continue
            
            # Check for bold (**text**)
            if text[i:i+2] == '**':
                end = text.find('**', i+2)
                if end != -1:
                    content = text[i+2:end]
                    tag = f"{base_tag}_bold" if base_tag != "body" else "bold"
                    text_widget.insert("end", content, tag)
                    i = end + 2
                    continue
            
            # Check for code (`text`)
            if text[i] == '`':
                end = text.find('`', i+1)
                if end != -1:
                    content = text[i+1:end]
                    tag = f"{base_tag}_code" if base_tag != "body" else "code"
                    text_widget.insert("end", content, tag)
                    i = end + 1
                    continue
            
            # Check for italic (*text*) - must check after ** to avoid conflicts
            if text[i] == '*':
                end = text.find('*', i+1)
                if end != -1:
                    content = text[i+1:end]
                    tag = f"{base_tag}_italic" if base_tag != "body" else "italic"
                    text_widget.insert("end", content, tag)
                    i = end + 1
                    continue
            
            # Regular character
            tag = base_tag
            text_widget.insert("end", text[i], tag)
            i += 1