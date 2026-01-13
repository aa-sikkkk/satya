import customtkinter as ctk

class ConceptDetailView(ctk.CTkFrame):
    def __init__(self, master, concept, on_start_questions, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_start_questions = on_start_questions
        self.on_back = on_back
        self.concept = concept

        # Main Title Area
        self.label = ctk.CTkLabel(
            self, 
            text=concept.get('name', 'Concept'), 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            wraplength=700
        )
        self.label.pack(pady=(30, 15))

        # Summary
        if concept.get('summary'):
            summary_frame = ctk.CTkFrame(self, fg_color="transparent")
            summary_frame.pack(pady=(0, 20), padx=40, fill='x')
            ctk.CTkLabel(
                summary_frame, 
                text=concept['summary'], 
                font=ctk.CTkFont(family="Segoe UI", size=15), 
                wraplength=600, 
                justify='left',
                text_color=("gray10", "gray85")
            ).pack()

        # Footer Frame 
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", fill="x", pady=20)

        self.start_btn = ctk.CTkButton(
            self.footer_frame, 
            text="Start Questions", 
            command=self.on_start_questions,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=50,
            width=200,
            corner_radius=25,
            fg_color="#43A047", # Green 600
            hover_color="#2E7D32" # Green 800
        )
        self.start_btn.pack(pady=(0, 10))
        
        self.back_btn = ctk.CTkButton(
            self.footer_frame, 
            text="Back", 
            command=self.on_back, 
            fg_color="transparent", 
            border_width=1, 
            border_color="#bdbdbd",
            text_color=("gray10", "#bdbdbd"),
            hover_color=("gray90", "gray20")
        )
        self.back_btn.pack(pady=(5, 0))

        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", width=700)
        self.content_frame.pack(pady=(0, 10), fill='both', expand=True)

        if concept.get('objectives'):
            ctk.CTkLabel(
                self.content_frame, 
                text="Learning Objectives", 
                font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                text_color="#3949AB"
            ).pack(pady=(10, 10), padx=20, anchor='w')
            
            for obj in concept['objectives']:
                ctk.CTkLabel(
                    self.content_frame, 
                    text=f"•  {obj}", 
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    wraplength=650,
                    justify="left"
                ).pack(anchor='w', padx=(30, 20), pady=2)

        if concept.get('key_points'):
            ctk.CTkLabel(
                self.content_frame, 
                text="Key Points", 
                font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                text_color="#3949AB"
            ).pack(pady=(20, 10), padx=20, anchor='w')
            
            for kp in concept['key_points']:
                ctk.CTkLabel(
                    self.content_frame, 
                    text=f"•  {kp}", 
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    wraplength=650,
                    justify="left"
                ).pack(anchor='w', padx=(30, 20), pady=2) 