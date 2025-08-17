import customtkinter as ctk

class ConceptView(ctk.CTkFrame):
    def __init__(self, master, concepts, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.concepts = concepts

        # Main title
        self.label = ctk.CTkLabel(self, text="Select a Concept", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        # Create scrollable frame for concepts
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=600, height=400)
        self.scrollable_frame.pack(pady=(0, 20), padx=20, fill='both', expand=True)

        # Add concept buttons and summaries to scrollable frame
        for concept in concepts:
            btn = ctk.CTkButton(self.scrollable_frame, text=concept['name'], width=320, command=lambda c=concept['name']: self.on_select(c))
            btn.pack(pady=8)
            if 'summary' in concept and concept['summary']:
                ctk.CTkLabel(self.scrollable_frame, text=concept['summary'], font=ctk.CTkFont(size=14), wraplength=400, justify='left').pack(pady=(0, 10))

        # Back button
        self.back_btn = ctk.CTkButton(self, text="Back to Topics", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(20, 30)) 