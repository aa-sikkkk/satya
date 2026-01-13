import customtkinter as ctk

class ConceptView(ctk.CTkFrame):
    def __init__(self, master, concepts, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.concepts = concepts

        # Main Title Area
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(40, 25))
        
        self.label = ctk.CTkLabel(
            self.header_frame, 
            text="Explore Concepts", 
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        )
        self.label.pack()
        
        ctk.CTkLabel(
            self.header_frame,
            text="Select a topic to dive deeper",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="gray70"
        ).pack(pady=(5, 0))

        # Back button
        self.back_btn = ctk.CTkButton(
            self, 
            text="Back to Topics", 
            command=self.on_back, 
            fg_color="transparent", 
            border_width=1, 
            border_color="#bdbdbd",
            text_color=("gray10", "#bdbdbd"),
            hover_color=("gray90", "gray20")
        )
        self.back_btn.pack(side="bottom", pady=(10, 30))

        # Scrollable container
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=650, height=400, fg_color="transparent")
        self.scrollable_frame.pack(pady=(0, 20), padx=20, fill='both', expand=True)

        # 2-column Grid Layout
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        # Initial Load
        self.update_concepts(concepts)

    def update_concepts(self, concepts):
        """Update the grid with new concepts."""
        self.concepts = concepts
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, concept in enumerate(concepts):
            btn = ctk.CTkButton(
                self.scrollable_frame, 
                text=concept['name'], 
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                height=60,
                corner_radius=12,
                fg_color="#3949AB", 
                hover_color="#303F9F",
                command=lambda c=concept['name']: self.on_select(c)
            )
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")