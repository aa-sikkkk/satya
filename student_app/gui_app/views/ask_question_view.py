import customtkinter as ctk

class AskQuestionView(ctk.CTkFrame):
    def __init__(self, master, on_submit, on_back, on_ask_openai, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_submit = on_submit
        self.on_back = on_back
        self.on_ask_openai = on_ask_openai
        self.spinner_animation_running = False

        self.label = ctk.CTkLabel(self, text="Ask a Question", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 10))

        # Question input
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
            # Always use medium for detailed answers
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
            chars = ["|", "/", "-", ""]
            self.spinner.configure(text=f"Thinking... {chars[index]}")
            next_index = (index + 1) % len(chars)
            self.after(100, self._animate_spinner, next_index)

    def _calculate_answer_height(self, answer_length):
        """Calculate appropriate height for answer textbox based on answer length."""
        # Base heights for different answer lengths
        height_map = {
            "very_short": 60,
            "short": 100,
            "medium": 150,
            "long": 250,
            "very_long": 350
        }
        return height_map.get(answer_length, 150)
    
    def append_answer_token(self, token):
        """Append a token to the streaming answer display."""
        if self.answer_box is None:
            # Initialize answer box for streaming
            self.streaming_answer = ""
            for widget in self.result_frame.winfo_children():
                widget.destroy()
            
            # Source information panel (if available, will be set later)
            self.answer_frame = ctk.CTkFrame(self.result_frame, fg_color="#e3f2fd", corner_radius=8)
            self.answer_frame.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            
            # Create answer textbox with dynamic height
            answer_height = self._calculate_answer_height("medium")  # Default to medium
            self.answer_box = ctk.CTkTextbox(self.answer_frame, width=600, height=answer_height, font=ctk.CTkFont(size=16), wrap='word')
            self.answer_box.pack(pady=(10, 10), padx=10, fill='both', expand=True)
        
        # Append token to answer
        self.streaming_answer += token
        self.answer_box.insert('end', token)
        self.answer_box.see('end')  # Auto-scroll to bottom
        self.update_idletasks()  # Force UI update
    
    def finalize_answer(self, confidence, hints=None, related=None, source_info=None, question=None):
        """Finalize the streaming answer display with confidence and metadata."""
        self.set_loading(False)
        
        # Generate and append diagram if needed (non-blocking)
        if question and self.streaming_answer:
            try:
                from system.diagrams import generate_and_append_diagram
                self.streaming_answer = generate_and_append_diagram(question, self.streaming_answer)
                # Update answer box with diagram if added
                if self.answer_box:
                    self.answer_box.delete("1.0", "end")
                    self.answer_box.insert("1.0", self.streaming_answer)
            except Exception as e:
                # Graceful fallback: continue with original answer if diagram generation fails
                import logging
                logging.getLogger(__name__).debug(f"Diagram generation failed: {e}")
        
        if self.answer_box is None:
            # Fallback if streaming didn't initialize
            self.set_result(self.streaming_answer, confidence, hints, related, source_info)
            return
        
        # Adjust height based on actual answer length
        answer_length = len(self.streaming_answer)
        if answer_length < 100:
            height = 80
        elif answer_length < 300:
            height = 120
        elif answer_length < 600:
            height = 180
        elif answer_length < 1000:
            height = 250
        else:
            height = 350
        
        # Update answer box height
        self.answer_box.configure(height=height, state="disabled")
        
        # Add source info if available
        if source_info and self.answer_frame:
            # Check if source label already exists
            source_exists = False
            for widget in self.answer_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and "Source:" in widget.cget("text"):
                    source_exists = True
                    break
            
            if not source_exists:
                source_label = ctk.CTkLabel(self.answer_frame, text=f"Source: {source_info}", font=ctk.CTkFont(size=12), text_color="#1976d2")
                source_label.pack(pady=(5, 0), padx=10, anchor='w', before=self.answer_box)
        
        # Confidence indicator - ONLY show if confidence < 70% (subtle warning)
        if confidence < 0.7:
            if confidence > 0.4:
                conf_color = "#fff9c4"  # Light yellow background
                conf_text_color = "#f57c00"  # Orange text
                conf_text = "⚠️ Moderate confidence"
            else:
                conf_color = "#ffebee"  # Light red background
                conf_text_color = "#c62828"  # Dark red text
                conf_text = "⚠️ Low confidence - please verify"
                self.openai_btn.configure(state="normal")
            
            # Small, subtle indicator in bottom-right
            conf_frame = ctk.CTkFrame(self.result_frame, fg_color=conf_color, corner_radius=6)
            conf_frame.pack(pady=(0, 5), padx=10, anchor='e')  # Right-aligned
            ctk.CTkLabel(
                conf_frame, 
                text=f"{conf_text} ({confidence*100:.0f}%)", 
                font=ctk.CTkFont(size=11),  # Smaller font
                text_color=conf_text_color
            ).pack(pady=3, padx=8)
        
        # Hints section
        if hints:
            hints_frame = ctk.CTkFrame(self.result_frame, fg_color="#f3e5f5", corner_radius=8)
            hints_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(hints_frame, text="💡 Hints:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#7b1fa2").pack(pady=(10, 5), padx=10, anchor='w')
            for hint in hints:
                ctk.CTkLabel(hints_frame, text=f"• {hint}", font=ctk.CTkFont(size=14), wraplength=580, justify='left').pack(anchor='w', padx=20, pady=2)
        
        # Related concepts section
        if related:
            related_frame = ctk.CTkFrame(self.result_frame, fg_color="#e8f5e8", corner_radius=8)
            related_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(related_frame, text="🔗 Related Concepts:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#388e3c").pack(pady=(10, 5), padx=10, anchor='w')
            for rel in related:
                ctk.CTkLabel(related_frame, text=f"• {rel}", font=ctk.CTkFont(size=14)).pack(anchor='w', padx=20, pady=2)
    
    def set_result(self, answer, confidence=None, hints=None, related=None, source_info=None, is_openai=False):
        """Set the complete answer result (non-streaming fallback)."""
        self.set_loading(False)
        self.streaming_answer = answer
        
        if not is_openai:
            for widget in self.result_frame.winfo_children():
                widget.destroy()
        
        if is_openai:
            source_info = "OpenAI (Online)"
            source_frame = ctk.CTkFrame(self.result_frame, fg_color="#d1c4e9", corner_radius=8)
            source_frame.pack(pady=(10, 10), padx=10, fill='x')
            ctk.CTkLabel(source_frame, text=f"Source: {source_info}", font=ctk.CTkFont(size=12), text_color="#512da8").pack(pady=5, padx=10, anchor='w')
            
            # Adjust height based on answer length
            answer_length = len(answer)
            height = self._calculate_answer_height("medium")
            if answer_length < 100:
                height = 60
            elif answer_length < 300:
                height = 100
            elif answer_length < 600:
                height = 150
            elif answer_length < 1000:
                height = 250
            else:
                height = 350
            
            answer_box = ctk.CTkTextbox(source_frame, width=600, height=height, font=ctk.CTkFont(size=15), wrap='word')
            answer_box.insert('1.0', answer)
            answer_box.configure(state="disabled")
            answer_box.pack(pady=(5, 10), padx=10, fill='x', expand=True)
            return

        # Source information panel
        if source_info:
            source_frame = ctk.CTkFrame(self.result_frame, fg_color="#e3f2fd", corner_radius=8)
            source_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(source_frame, text=f"Source: {source_info}", font=ctk.CTkFont(size=12), text_color="#1976d2").pack(pady=5, padx=10, anchor='w')
        
        if confidence is None or confidence < 0.3:  # Raised from 0.1 to avoid false warnings
            # Yellow warning panel for low confidence
            warn_frame = ctk.CTkFrame(self.result_frame, fg_color="#fffde7", corner_radius=8)
            warn_frame.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            ctk.CTkLabel(warn_frame, text="I'm not sure about that. Let me help you find the right information:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#fbc02d").pack(pady=(10, 0), padx=10, anchor='w')
            
            # Adjust height based on answer length
            answer_length = len(answer)
            height = 80 if answer_length < 200 else (150 if answer_length < 500 else 250)
            
            answer_box = ctk.CTkTextbox(warn_frame, width=600, height=height, font=ctk.CTkFont(size=15), wrap='word')
            answer_box.insert('1.0', answer)
            answer_box.configure(state="disabled")
            answer_box.pack(pady=(5, 10), padx=10, fill='x', expand=True)
            self.openai_btn.configure(state="normal")
        else:
            # Normal answer panel with dynamic height
            answer_length = len(answer)
            if answer_length < 100:
                height = 80
            elif answer_length < 300:
                height = 120
            elif answer_length < 600:
                height = 180
            elif answer_length < 1000:
                height = 250
            else:
                height = 350
            
            self.answer_box = ctk.CTkTextbox(self.result_frame, width=600, height=height, font=ctk.CTkFont(size=16), wrap='word')
            self.answer_box.insert('1.0', answer)
            self.answer_box.configure(state="disabled")
            self.answer_box.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            
            # Confidence indicator - ONLY show if confidence < 70% (subtle warning)
            if confidence < 0.7:
                if confidence > 0.4:
                    conf_color = "#fff9c4"  # Light yellow background
                    conf_text_color = "#f57c00"  # Orange text
                    conf_text = "⚠️ Moderate confidence"
                else:
                    conf_color = "#ffebee"  # Light red background
                    conf_text_color = "#c62828"  # Dark red text
                    conf_text = "⚠️ Low confidence - please verify"
                    self.openai_btn.configure(state="normal")
                
                # Small, subtle indicator in bottom-right
                conf_frame = ctk.CTkFrame(self.result_frame, fg_color=conf_color, corner_radius=6)
                conf_frame.pack(pady=(0, 5), padx=10, anchor='e')  # Right-aligned
                ctk.CTkLabel(
                    conf_frame, 
                    text=f"{conf_text} ({confidence*100:.0f}%)", 
                    font=ctk.CTkFont(size=11),  # Smaller font
                    text_color=conf_text_color
                ).pack(pady=3, padx=8)
        
        # Hints section
        if hints:
            hints_frame = ctk.CTkFrame(self.result_frame, fg_color="#f3e5f5", corner_radius=8)
            hints_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(hints_frame, text="💡 Hints:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#7b1fa2").pack(pady=(10, 5), padx=10, anchor='w')
            for hint in hints:
                ctk.CTkLabel(hints_frame, text=f"• {hint}", font=ctk.CTkFont(size=14), wraplength=580, justify='left').pack(anchor='w', padx=20, pady=2)
        
        # Related concepts section
        if related:
            related_frame = ctk.CTkFrame(self.result_frame, fg_color="#e8f5e8", corner_radius=8)
            related_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(related_frame, text="🔗 Related Concepts:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#388e3c").pack(pady=(10, 5), padx=10, anchor='w')
            for rel in related:
                ctk.CTkLabel(related_frame, text=f"• {rel}", font=ctk.CTkFont(size=14)).pack(anchor='w', padx=20, pady=2)

    