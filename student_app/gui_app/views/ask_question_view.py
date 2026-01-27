# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

import customtkinter as ctk

class AskQuestionView(ctk.CTkScrollableFrame):
    def __init__(self, master, on_submit, on_back, on_ask_openai, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_submit = on_submit
        self.on_back = on_back
        self.on_ask_openai = on_ask_openai
        self.spinner_animation_running = False

        self.label = ctk.CTkLabel(self, text="Ask a Question", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 5))

        self.guide_frame = ctk.CTkFrame(self, fg_color="#E8EAF6", corner_radius=12)
        self.guide_frame.pack(pady=(0, 25), padx=40, fill='x')
        
        ctk.CTkLabel(
            self.guide_frame, 
            text="Tips for best results", 
            font=ctk.CTkFont(size=15, weight="bold"), 
            text_color="#3949AB"
        ).pack(pady=(12, 5))
        
        ctk.CTkLabel(
            self.guide_frame, 
            text="• Use 'Describe' or 'Explain' for detail\n• Be specific and use textbook terms\n• Powered by your offline notes", 
            font=ctk.CTkFont(size=13), 
            text_color="#5C6BC0", # Indigo-400
            justify="center"
        ).pack(pady=(0, 12))

        self.entry = ctk.CTkEntry(self, placeholder_text="Type your question here...", width=400, font=ctk.CTkFont(size=16))
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', lambda e: self.submit())

        self.submit_btn = ctk.CTkButton(self, text="Ask", command=self.submit)
        self.submit_btn.pack(pady=10)

        self.result_frame = ctk.CTkFrame(self)
        self.result_frame.pack(pady=20, fill='x', expand=True)

        self.spinner = None
        self.answer_box = None
        self.answer_frame = None
        self.streaming_answer = ""
        
        self.openai_btn = ctk.CTkButton(self, text="Ask OpenAI", command=self.ask_openai, state="disabled")
        self.openai_btn.pack(pady=10)

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(30, 0))

    def submit(self):
        question = self.entry.get().strip()
        if question:
            self.set_loading(True)    
            self.on_submit(question, "medium")
            
    def ask_openai(self):
        question = self.entry.get().strip()
        if question:
            self.set_loading(True)
            self.on_ask_openai(question)

    def set_loading(self, loading):
        if loading:
            self.entry.configure(state="disabled")
            self.submit_btn.configure(state="disabled")
            self.openai_btn.configure(state="disabled")
            for widget in self.result_frame.winfo_children():
                widget.destroy()
            self.answer_box = None
            self.answer_frame = None
            self.streaming_answer = ""
            self.spinner = ctk.CTkLabel(self.result_frame, text="", font=ctk.CTkFont(size=16))
            self.spinner.pack(pady=20)
            self.spinner_animation_running = True
            self._animate_spinner(0)
        else:
            self.entry.configure(state="normal")
            self.submit_btn.configure(state="normal")
            if self.spinner:
                self.spinner.destroy()
                self.spinner = None
            self.spinner_animation_running = False

    def _animate_spinner(self, index):
        if self.spinner_animation_running and self.spinner and self.spinner.winfo_exists():
            chars = ["|", "/", "-", "\\"]
            self.spinner.configure(text=f"Thinking... {chars[index]}")
            next_index = (index + 1) % len(chars)
            self.after(100, self._animate_spinner, next_index)

    def _calculate_fluid_height(self, text):
        """Calculate exact height needed for text content."""
        if not text:
            return 80
        
        # More accurate character counting
        chars_per_line = 70  # Adjusted for typical textbox width
        total_lines = 0
        
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                total_lines += 1  # Empty line
            else:
                # Calculate wrapped lines for this paragraph
                total_lines += max(1, (len(paragraph) + chars_per_line - 1) // chars_per_line)
        
        # More accurate line height and padding
        line_height = 22  # Reduced from 28
        padding = 40      # Reduced from 50
        calculated_height = (total_lines * line_height) + padding
        
        # Set reasonable bounds - max 600px instead of 1200px
        return max(100, min(calculated_height, 600))
    
    def append_answer_token(self, token):
        """Append a token to the streaming answer display."""
        if self.answer_box is None:
            self.streaming_answer = ""
            for widget in self.result_frame.winfo_children():
                widget.destroy()
            
            self.answer_frame = ctk.CTkFrame(self.result_frame, fg_color="#e3f2fd", corner_radius=8)
            self.answer_frame.pack(pady=(0, 10), padx=10, fill='x', expand=False)
            
            starting_height = 120
            self.answer_box = ctk.CTkTextbox(
                self.answer_frame, 
                width=600, 
                height=starting_height, 
                font=ctk.CTkFont(size=14), 
                wrap='word'
            )
            self.answer_box.pack(pady=(10, 10), padx=10, fill='x', expand=False)
        
        self.streaming_answer += token
        self.answer_box.insert('end', token)
        self.answer_box.see('end')
        
        # Dynamically adjust height during streaming
        if len(self.streaming_answer) % 100 == 0:
            new_height = self._calculate_fluid_height(self.streaming_answer)
            if new_height > self.answer_box.cget("height"):
                self.answer_box.configure(height=new_height)
                
        self.update_idletasks()
    
    def finalize_answer(self, confidence, hints=None, related=None, source_info=None, question=None, rag_chunks=None, llm_handler=None):
        self.set_loading(False)
        
        # Generate diagram if applicable (Background Thread)
        if question and self.streaming_answer:
            try:
                # Show analyzing indicator - pack it in answer_frame after the answer box
                self.analyzing_label = ctk.CTkLabel(
                    self.answer_frame if self.answer_frame else self.result_frame,
                    text="⚡ Analyzing for visual representation...",
                    font=ctk.CTkFont(size=12, slant="italic"),
                    text_color="#78909c"
                )
                self.analyzing_label.pack(pady=(5, 10), padx=10, anchor='w')
                
                # Run generation in background thread
                import threading
                threading.Thread(
                    target=self._generate_diagram_background,
                    args=(question, self.streaming_answer, rag_chunks, llm_handler),
                    daemon=True
                ).start()
                
            except Exception as e:
                print(f"DEBUG: Failed to start background diagram thread: {e}")

        # If no streaming box exists, fall back to complete render
        if self.answer_box is None:
            self._render_complete_answer(
                self.streaming_answer, 
                confidence, 
                hints, 
                related, 
                source_info, 
                is_openai=False
            )
            return
        
        # Get the actual required height from the textbox content
        # The textbox knows how much space it needs
        self.answer_box.update_idletasks()
        
        # Count actual lines in the textbox
        line_count = int(self.answer_box.index('end-1c').split('.')[0])
        
        # Calculate height based on actual line count (not estimated)
        line_height = 22
        padding = 40
        final_height = max(100, min((line_count * line_height) + padding, 600))
        
        self.answer_box.configure(height=final_height, state="disabled")
        
        # Force update to finalize the answer_frame size
        self.answer_frame.update_idletasks()
        
        if source_info and self.answer_frame:
            source_exists = any(
                isinstance(w, ctk.CTkLabel) and "Source:" in w.cget("text")
                for w in self.answer_frame.winfo_children()
            )
            
            if not source_exists:
                source_label = ctk.CTkLabel(
                    self.answer_frame, 
                    text=f"Source: {source_info}", 
                    font=ctk.CTkFont(size=12), 
                    text_color="#1976d2"
                )
                source_label.pack(pady=(5, 0), padx=10, anchor='w', before=self.answer_box)
        
        # Add confidence, hints, and related concepts
        self._add_metadata_sections(confidence, hints, related)

    def _generate_diagram_background(self, question, answer, rag_chunks, llm_handler):
        """Runs diagram generation in a separate thread."""
        try:
            print("DEBUG: Starting background diagram generation...")
            from system.diagrams import generate_diagram_content
            result = generate_diagram_content(
                question, 
                answer,
                rag_chunks=rag_chunks,
                llm_handler=llm_handler
            )
            # Schedule UI update on main thread
            self.after(0, self._on_diagram_generated, result)
        except Exception as e:
            print(f"DEBUG: Background generation failed: {e}")
            self.after(0, self._on_diagram_generated, None)

    def _on_diagram_generated(self, result):
        """Callback to update UI with generated diagram."""
        # Remove analyzing label
        if hasattr(self, 'analyzing_label') and self.analyzing_label:
            self.analyzing_label.destroy()
            
        if result:
            formatted_diagram, diagram_type = result
            print(f"DEBUG: Diagram generated in background. Type: {diagram_type}")
            
            # Create diagram as a SEPARATE frame in result_frame (sibling to answer_frame, not child)
            # This prevents the answer box from expanding when diagram is added
            self.diagram_frame = ctk.CTkFrame(self.result_frame, fg_color="#fff3e0", corner_radius=8)
            self.diagram_frame.pack(pady=(0, 10), padx=10, fill='x', expand=False)
            
            type_name = diagram_type.value if hasattr(diagram_type, 'value') else str(diagram_type)
            ctk.CTkLabel(
                self.diagram_frame, 
                text=f"Visual Representation ({type_name.title()})", 
                font=ctk.CTkFont(size=14, weight="bold"), 
                text_color="#e65100"
            ).pack(pady=(10, 5), padx=10, anchor='w')
            
            diagram_box = ctk.CTkTextbox(
                self.diagram_frame, 
                width=600, 
                height=300, 
                font=ctk.CTkFont(family="Consolas", size=12), 
                wrap='none'
            )
            diagram_box.insert("1.0", formatted_diagram)
            diagram_box.configure(state="disabled")
            diagram_box.pack(pady=(0, 10), padx=10, fill='x', expand=False)
    
    def set_result(self, answer, confidence=None, hints=None, related=None, source_info=None, is_openai=False):
        """Complete answer result (non-streaming fallback)."""
        self.set_loading(False)
        self.streaming_answer = answer
        
        if not is_openai:
            for widget in self.result_frame.winfo_children():
                widget.destroy()
        
        self._render_complete_answer(answer, confidence, hints, related, source_info, is_openai)
    
    def _render_complete_answer(self, answer, confidence, hints, related, source_info, is_openai):
        """Method to render complete answer with all metadata."""
        height = self._calculate_fluid_height(answer)
        
        # OpenAI response styling
        if is_openai:
            source_info = "OpenAI (Online)"
            source_frame = ctk.CTkFrame(self.result_frame, fg_color="#d1c4e9", corner_radius=8)
            source_frame.pack(pady=(10, 10), padx=10, fill='x')
            
            ctk.CTkLabel(
                source_frame, 
                text=f"Source: {source_info}", 
                font=ctk.CTkFont(size=12), 
                text_color="#512da8"
            ).pack(pady=5, padx=10, anchor='w')
            
            answer_box = ctk.CTkTextbox(source_frame, width=600, height=height, font=ctk.CTkFont(size=14), wrap='word')
            answer_box.insert('1.0', answer)
            answer_box.configure(state="disabled")
            answer_box.pack(pady=(5, 10), padx=10, fill='x', expand=True)
            return
        
        # Source information panel
        if source_info:
            source_frame = ctk.CTkFrame(self.result_frame, fg_color="#e3f2fd", corner_radius=8)
            source_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(
                source_frame, 
                text=f"Source: {source_info}", 
                font=ctk.CTkFont(size=12), 
                text_color="#1976d2"
            ).pack(pady=5, padx=10, anchor='w')
        
        # Very low confidence warning
        if confidence is None or confidence < 0.3:
            warn_frame = ctk.CTkFrame(self.result_frame, fg_color="#fffde7", corner_radius=8)
            warn_frame.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            
            ctk.CTkLabel(
                warn_frame, 
                text="I'm not sure about that. Let me help you find the right information:", 
                font=ctk.CTkFont(size=15, weight="bold"), 
                text_color="#fbc02d"
            ).pack(pady=(10, 0), padx=10, anchor='w')
            
            answer_box = ctk.CTkTextbox(warn_frame, width=600, height=height, font=ctk.CTkFont(size=14), wrap='word')
            answer_box.insert('1.0', answer)
            answer_box.configure(state="disabled")
            answer_box.pack(pady=(5, 10), padx=10, fill='x', expand=True)
            self.openai_btn.configure(state="normal")
        else:
            # Normal answer box
            self.answer_box = ctk.CTkTextbox(
                self.result_frame, 
                width=600, 
                height=height, 
                font=ctk.CTkFont(size=14), 
                wrap='word'
            )
            self.answer_box.insert('1.0', answer)
            
            self.answer_box.configure(state="disabled")
            self.answer_box.pack(pady=(0, 10), padx=10, fill='x', expand=True)
        
        # Add confidence, hints, and related concepts
        self._add_metadata_sections(confidence, hints, related)
    
    def _add_metadata_sections(self, confidence, hints, related):
        """Add confidence indicator, hints, and related concepts sections."""
        # Confidence indicator
        if confidence and confidence < 0.7:
            if confidence > 0.4:
                conf_color = "#fff9c4"
                conf_text_color = "#f57c00"
                conf_text = "⚠️ Moderate confidence"
            else:
                conf_color = "#ffebee"
                conf_text_color = "#c62828"
                conf_text = "⚠️ Low confidence - please verify"
                self.openai_btn.configure(state="normal")
            
            conf_frame = ctk.CTkFrame(self.result_frame, fg_color=conf_color, corner_radius=6)
            conf_frame.pack(pady=(0, 5), padx=10, anchor='e')
            ctk.CTkLabel(
                conf_frame, 
                text=f"{conf_text} ({confidence*100:.0f}%)", 
                font=ctk.CTkFont(size=11), 
                text_color=conf_text_color
            ).pack(pady=3, padx=8)
        
        # Hints section
        if hints:
            hints_frame = ctk.CTkFrame(self.result_frame, fg_color="#f3e5f5", corner_radius=8)
            hints_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(
                hints_frame, 
                text="💡 Hints:", 
                font=ctk.CTkFont(size=15, weight="bold"), 
                text_color="#7b1fa2"
            ).pack(pady=(10, 5), padx=10, anchor='w')
            
            for hint in hints:
                ctk.CTkLabel(
                    hints_frame, 
                    text=f"• {hint}", 
                    font=ctk.CTkFont(size=14), 
                    wraplength=580, 
                    justify='left'
                ).pack(anchor='w', padx=20, pady=2)
        
        # Related concepts section
        if related:
            related_frame = ctk.CTkFrame(self.result_frame, fg_color="#e8f5e8", corner_radius=8)
            related_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(
                related_frame, 
                text="🔗 Related Concepts:", 
                font=ctk.CTkFont(size=15, weight="bold"), 
                text_color="#388e3c"
            ).pack(pady=(10, 5), padx=10, anchor='w')
            
            for rel in related:
                ctk.CTkLabel(
                    related_frame, 
                    text=f"• {rel}", 
                    font=ctk.CTkFont(size=14)
                ).pack(anchor='w', padx=20, pady=2)