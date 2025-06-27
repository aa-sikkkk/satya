import customtkinter as ctk

class ConceptDetailView(ctk.CTkFrame):
    def __init__(self, master, concept, on_start_questions, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_start_questions = on_start_questions
        self.on_back = on_back
        self.concept = concept

        self.label = ctk.CTkLabel(self, text=concept.get('name', 'Concept'), font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 10))

        if concept.get('summary'):
            ctk.CTkLabel(self, text=concept['summary'], font=ctk.CTkFont(size=15), wraplength=500, justify='left').pack(pady=(0, 10))
        if concept.get('objectives'):
            ctk.CTkLabel(self, text="Learning Objectives:", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 0))
            for obj in concept['objectives']:
                ctk.CTkLabel(self, text=f"• {obj}", font=ctk.CTkFont(size=14)).pack(anchor='w', padx=40)
        if concept.get('key_points'):
            ctk.CTkLabel(self, text="Key Points:", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 0))
            for kp in concept['key_points']:
                ctk.CTkLabel(self, text=f"• {kp}", font=ctk.CTkFont(size=14)).pack(anchor='w', padx=40)

        self.start_btn = ctk.CTkButton(self, text="Start Questions", command=self.on_start_questions)
        self.start_btn.pack(pady=20)
        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(10, 0)) 