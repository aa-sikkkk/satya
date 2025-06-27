import customtkinter as ctk

class AskQuestionView(ctk.CTkFrame):
    def __init__(self, master, on_submit, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_submit = on_submit
        self.on_back = on_back

        self.label = ctk.CTkLabel(self, text="Ask a Question", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 10))

        self.entry = ctk.CTkEntry(self, placeholder_text="Type your question here...", width=400, font=ctk.CTkFont(size=16))
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', lambda e: self.submit())

        self.submit_btn = ctk.CTkButton(self, text="Ask", command=self.submit)
        self.submit_btn.pack(pady=10)

        self.result_frame = ctk.CTkFrame(self)
        self.result_frame.pack(pady=20, fill='x', expand=True)

        self.spinner = None
        self.answer_box = None

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(30, 0))

    def submit(self):
        question = self.entry.get().strip()
        if question:
            self.set_loading(True)
            self.on_submit(question)

    def set_loading(self, loading):
        if loading:
            self.entry.configure(state="disabled")
            self.submit_btn.configure(state="disabled")
            for widget in self.result_frame.winfo_children():
                widget.destroy()
            self.spinner = ctk.CTkLabel(self.result_frame, text="Thinking... ⏳", font=ctk.CTkFont(size=16))
            self.spinner.pack(pady=20)
        else:
            self.entry.configure(state="normal")
            self.submit_btn.configure(state="normal")
            if self.spinner:
                self.spinner.destroy()
                self.spinner = None

    def set_result(self, answer, confidence=None, hints=None, related=None):
        self.set_loading(False)
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        if confidence is None or confidence < 0.1:
            # Yellow warning panel
            warn_frame = ctk.CTkFrame(self.result_frame, fg_color="#fffde7", corner_radius=8)
            warn_frame.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            ctk.CTkLabel(warn_frame, text="I'm not sure about that. Let me help you find the right information:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#fbc02d").pack(pady=(10, 0), padx=10, anchor='w')
            answer_box = ctk.CTkTextbox(warn_frame, width=600, height=80, font=ctk.CTkFont(size=15), wrap='word')
            answer_box.insert('1.0', answer)
            answer_box.configure(state="disabled")
            answer_box.pack(pady=(5, 10), padx=10, fill='x', expand=True)
        else:
            # Normal answer panel
            self.answer_box = ctk.CTkTextbox(self.result_frame, width=600, height=100, font=ctk.CTkFont(size=16), wrap='word')
            self.answer_box.insert('1.0', answer)
            self.answer_box.configure(state="disabled")
            self.answer_box.pack(pady=(0, 10), padx=10, fill='x', expand=True)
            color = '#43a047' if confidence > 0.7 else '#fbc02d' if confidence > 0.4 else '#e53935'
            ctk.CTkLabel(self.result_frame, text=f"Confidence: {confidence*100:.1f}%", font=ctk.CTkFont(size=14), text_color=color).pack()
        if hints:
            ctk.CTkLabel(self.result_frame, text="Hints:", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 0))
            for hint in hints:
                ctk.CTkLabel(self.result_frame, text=f"• {hint}", font=ctk.CTkFont(size=14), wraplength=580, justify='left').pack(anchor='w', padx=40)
        if related:
            ctk.CTkLabel(self.result_frame, text="Related Concepts:", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 0))
            for rel in related:
                ctk.CTkLabel(self.result_frame, text=f"• {rel}", font=ctk.CTkFont(size=14)).pack(anchor='w', padx=40) 