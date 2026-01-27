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
