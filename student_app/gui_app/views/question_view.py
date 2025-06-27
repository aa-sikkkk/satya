import customtkinter as ctk

class QuestionView(ctk.CTkFrame):
    def __init__(self, master, question, on_submit, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_submit = on_submit
        self.on_back = on_back
        self.question = question

        self.label = ctk.CTkLabel(self, text="Question", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 10))
        self.q_text = ctk.CTkLabel(self, text=question, font=ctk.CTkFont(size=18), wraplength=600, justify='left')
        self.q_text.pack(pady=(0, 20), padx=20)

        self.answer_entry = ctk.CTkEntry(self, placeholder_text="Your answer", width=350, font=ctk.CTkFont(size=16))
        self.answer_entry.pack(pady=10)
        self.answer_entry.bind('<Return>', lambda e: self.submit())

        self.submit_btn = ctk.CTkButton(self, text="Submit", command=self.submit)
        self.submit_btn.pack(pady=20)

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(30, 0))

    def submit(self):
        answer = self.answer_entry.get().strip()
        self.on_submit(answer) 