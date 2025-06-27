import customtkinter as ctk

class ConceptView(ctk.CTkFrame):
    def __init__(self, master, concepts, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.concepts = concepts

        self.label = ctk.CTkLabel(self, text="Select a Concept", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        for concept in concepts:
            btn = ctk.CTkButton(self, text=concept['name'], width=320, command=lambda c=concept['name']: self.on_select(c))
            btn.pack(pady=8)
            if 'summary' in concept and concept['summary']:
                ctk.CTkLabel(self, text=concept['summary'], font=ctk.CTkFont(size=14), wraplength=400, justify='left').pack(pady=(0, 10))

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(40, 0)) 