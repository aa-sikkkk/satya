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

    def set_result(self, answer, confidence=None, hints=None, related=None, source_info=None, is_openai=False):
        self.set_loading(False)
        if not is_openai:
            for widget in self.result_frame.winfo_children():
                widget.destroy()
        
        if is_openai:
            source_info = "OpenAI (Online)"
            source_frame = ctk.CTkFrame(self.result_frame, fg_color="#d1c4e9", corner_radius=8)
            source_frame.pack(pady=(10, 10), padx=10, fill='x')
            ctk.CTkLabel(source_frame, text=f"Source: {source_info}", font=ctk.CTkFont(size=12), text_color="#512da8").pack(pady=5, padx=10, anchor='w')
            
            answer_box = ctk.CTkTextbox(source_frame, width=600, height=80, font=ctk.CTkFont(size=15), wrap='word')
            answer_box.insert('1.0', answer)
            answer_box.configure(state="disabled")
            answer_box.pack(pady=(5, 10), padx=10, fill='x', expand=True)
            return

        # Source information panel
        if source_info:
            source_frame = ctk.CTkFrame(self.result_frame, fg_color="#e3f2fd", corner_radius=8)
            source_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(source_frame, text=f"Source: {source_info}", font=ctk.CTkFont(size=12), text_color="#1976d2").pack(pady=5, padx=10, anchor='w')
        
        if confidence is None or confidence < 0.1:
            # Yellow warning panel for low confidence
            warn_frame = ctk.CTkFrame(self.result_frame, fg_color="#fffde7", corner_radius=8)
            warn_frame.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            ctk.CTkLabel(warn_frame, text="I'm not sure about that. Let me help you find the right information:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#fbc02d").pack(pady=(10, 0), padx=10, anchor='w')
            answer_box = ctk.CTkTextbox(warn_frame, width=600, height=80, font=ctk.CTkFont(size=15), wrap='word')
            answer_box.insert('1.0', answer)
            answer_box.configure(state="disabled")
            answer_box.pack(pady=(5, 10), padx=10, fill='x', expand=True)
            self.openai_btn.configure(state="normal")
        else:
            # Normal answer panel
            self.answer_box = ctk.CTkTextbox(self.result_frame, width=600, height=100, font=ctk.CTkFont(size=16), wrap='word')
            self.answer_box.insert('1.0', answer)
            self.answer_box.configure(state="disabled")
            self.answer_box.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            
            # Confidence indicator with color coding
            if confidence > 0.7:
                conf_color = "#43a047"  # Green
                conf_text = "High Confidence"
            elif confidence > 0.4:
                conf_color = "#fbc02d"  # Yellow
                conf_text = "Medium Confidence"
            else:
                conf_color = "#e53935"  # Red
                conf_text = "Low Confidence"
                self.openai_btn.configure(state="normal")
            
            conf_frame = ctk.CTkFrame(self.result_frame, fg_color=conf_color, corner_radius=4)
            conf_frame.pack(pady=(0, 10), padx=10, fill='x')
            ctk.CTkLabel(conf_frame, text=f"{conf_text}: {confidence*100:.1f}%", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(pady=5, padx=10)
        
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

    