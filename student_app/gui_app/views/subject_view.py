import customtkinter as ctk

class SubjectView(ctk.CTkFrame):
    def __init__(self, master, subjects, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.subjects = subjects

        self.label = ctk.CTkLabel(self, text="Select a Subject", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        self.subject_buttons = []
        for subj in subjects:
            btn = ctk.CTkButton(self, text=subj, width=220, command=lambda s=subj: self.on_select(s))
            btn.pack(pady=8)
            self.subject_buttons.append(btn)

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(40, 0)) 