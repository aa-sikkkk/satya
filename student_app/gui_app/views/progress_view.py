import customtkinter as ctk

class ProgressView(ctk.CTkFrame):
    def __init__(self, master, stats, mastered, weak, subject_stats, next_concept, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_back = on_back
        
        self.COLOR_PRIMARY = "#1A237E"    # Deep Indigo
        self.COLOR_ACCENT = "#283593"     # Lighter Indigo
        self.COLOR_SUCCESS = "#2E7D32"    # Emerald Green
        self.COLOR_WARNING = "#C62828"    # Deep Red
        self.COLOR_NEUTRAL = "#424242"    # Dark Grey
        self.COLOR_BG_CARD = "#FFFFFF"    # White
        self.COLOR_TEXT_LIGHT = "#757575" # Light Grey Text
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 20))
        
        ctk.CTkLabel(
            header_frame, 
            text="Your Learning Journey 🚀", 
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.COLOR_PRIMARY
        ).pack(anchor='w')
        
        ctk.CTkLabel(
            header_frame, 
            text="Track your mastery, identify weak spots, and keep growing.", 
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.COLOR_TEXT_LIGHT
        ).pack(anchor='w', pady=(2, 0))

        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        stats_grid = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        stats_grid.pack(fill='x', padx=10, pady=(10, 20))
        
        def create_stat_card(parent, icon, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=self.COLOR_BG_CARD, corner_radius=15, border_width=1, border_color="#E0E0E0")
            card.pack(side='left', fill='both', expand=True, padx=10)
            
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(expand=True, pady=20)
            
            ctk.CTkLabel(content, text=icon, font=ctk.CTkFont(size=32)).pack(pady=(0, 5))
            ctk.CTkLabel(content, text=value, font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=color).pack()
            ctk.CTkLabel(content, text=title, font=ctk.CTkFont(family="Segoe UI", size=13), text_color=self.COLOR_TEXT_LIGHT).pack()

        create_stat_card(stats_grid, "📝", "Questions Answered", str(stats['total']), self.COLOR_PRIMARY)
        create_stat_card(stats_grid, "✅", "Correct Answers", str(stats['correct']), self.COLOR_SUCCESS)
        create_stat_card(stats_grid, "🎯", "Overall Accuracy", f"{stats['score']:.1f}%", self.COLOR_ACCENT)

        concepts_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        concepts_frame.pack(fill='x', padx=10, pady=10)
        
        mastered_col = ctk.CTkFrame(concepts_frame, fg_color="transparent")
        mastered_col.pack(side='left', fill='both', expand=True, padx=(10, 10))
        self._create_section_header(mastered_col, "🏆 Mastered Concepts", self.COLOR_SUCCESS)
        
        m_content = ctk.CTkFrame(mastered_col, fg_color=self.COLOR_BG_CARD, corner_radius=15, border_width=1, border_color="#E0E0E0")
        m_content.pack(fill='both', expand=True, pady=10)
        
        if mastered:
            self._create_chip_grid(m_content, mastered, "#E8F5E9", "#2E7D32") # Light Green BG, Dark Green Text
        else:
            self._create_empty_state(m_content, "Keep practicing to master concepts!")

        weak_col = ctk.CTkFrame(concepts_frame, fg_color="transparent")
        weak_col.pack(side='left', fill='both', expand=True, padx=(10, 10))
        self._create_section_header(weak_col, "🧠 Focus Areas", self.COLOR_WARNING)
        
        w_content = ctk.CTkFrame(weak_col, fg_color=self.COLOR_BG_CARD, corner_radius=15, border_width=1, border_color="#E0E0E0")
        w_content.pack(fill='both', expand=True, pady=10)
        
        if weak:
            self._create_chip_grid(w_content, weak, "#FFEBEE", "#C62828") # Light Red BG, Dark Red Text
        else:
             self._create_empty_state(w_content, "Great job! No weak areas detected.", "🎉")

        subj_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        subj_frame.pack(fill='x', padx=20, pady=(20, 10))
        self._create_section_header(subj_frame, "📊 Subject Performance", self.COLOR_ACCENT)
        
        subj_card = ctk.CTkFrame(subj_frame, fg_color=self.COLOR_BG_CARD, corner_radius=15, border_width=1, border_color="#E0E0E0")
        subj_card.pack(fill='x', pady=10)
        
        if subject_stats:
            for i, (subject, s_data) in enumerate(subject_stats.items()):
                self._create_subject_row(subj_card, subject, s_data, i == len(subject_stats)-1)
        else:
            self._create_empty_state(subj_card, "No data yet. Start a quiz!")

        if next_concept:
            rec_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#E3F2FD", corner_radius=15, border_width=1, border_color="#BBDEFB")
            rec_frame.pack(fill='x', padx=20, pady=20)
            
            ctk.CTkLabel(rec_frame, text="💡 Recommendation", font=ctk.CTkFont(weight="bold"), text_color="#1565C0").pack(pady=(15, 5))
            ctk.CTkLabel(rec_frame, text=next_concept, font=ctk.CTkFont(size=14), text_color="#0D47A1").pack(pady=(0, 15))
        
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=20)
        
        self.back_btn = ctk.CTkButton(
            footer_frame, 
            text="← Back to Menu", 
            command=self.on_back,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=45,
            fg_color="transparent",
            border_width=1,
            border_color="#BDBDBD",
            text_color="#616161",
            hover_color="#F5F5F5"
        )
        self.back_btn.pack(side='left')
        
        self._bind_mouse_wheel(self.scrollable_frame)

    def _bind_mouse_wheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        widget.bind("<Button-4>", self._on_mouse_wheel)
        widget.bind("<Button-5>", self._on_mouse_wheel)
        
        for child in widget.winfo_children():
            self._bind_mouse_wheel(child)

    def _on_mouse_wheel(self, event):
        try:
            scroll_amount = 0
            if event.delta:
                if event.delta > 0:
                    scroll_amount = -1
                else:
                    scroll_amount = 1
            elif event.num == 4:
                scroll_amount = -1
            elif event.num == 5:
                scroll_amount = 1
                
            if scroll_amount != 0:
                self.scrollable_frame._parent_canvas.yview_scroll(scroll_amount, "units")
        except Exception:
            pass

    def _create_section_header(self, parent, text, color):
        label = ctk.CTkLabel(
            parent, 
            text=text, 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), 
            text_color=color
        )
        label.pack(anchor='w', padx=5)
        self._bind_mouse_wheel(label)

    def _create_empty_state(self, parent, text, icon="ℹ️"):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(expand=True, pady=30)
        
        l1 = ctk.CTkLabel(frame, text=icon, font=ctk.CTkFont(size=24))
        l1.pack(pady=(0,5))
        
        l2 = ctk.CTkLabel(frame, text=text, text_color=self.COLOR_TEXT_LIGHT)
        l2.pack()
        
        self._bind_mouse_wheel(frame)
        self._bind_mouse_wheel(l1)
        self._bind_mouse_wheel(l2)

    def _create_chip_grid(self, parent, items, bg_color, text_color):
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill='both', expand=True, padx=15, pady=15)
        self._bind_mouse_wheel(grid)
        
        for item in items:
            chip = ctk.CTkFrame(grid, fg_color=bg_color, corner_radius=20)
            chip.pack(anchor='w', pady=4)
            
            label = ctk.CTkLabel(
                chip, 
                text=f"  {item}  ", 
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=text_color
            )
            label.pack(pady=4, padx=8)
            
            self._bind_mouse_wheel(chip)
            self._bind_mouse_wheel(label)

    def _create_subject_row(self, parent, subject, data, is_last):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill='x', padx=20, pady=12)
        
        header = ctk.CTkFrame(row, fg_color="transparent")
        header.pack(fill='x', pady=(0, 5))
        
        l1 = ctk.CTkLabel(header, text=subject, font=ctk.CTkFont(weight="bold", size=14))
        l1.pack(side='left')
        
        l2 = ctk.CTkLabel(header, text=f"{data['pct']:.1f}%", font=ctk.CTkFont(weight="bold", size=14), text_color=self.COLOR_ACCENT)
        l2.pack(side='right')
        
        bar = ctk.CTkProgressBar(row, height=10, corner_radius=5)
        bar.set(data['pct'] / 100)
        bar.pack(fill='x')
        
        l3 = ctk.CTkLabel(
            row, 
            text=f"{data['correct']} / {data['total']} correct", 
            font=ctk.CTkFont(size=12), 
            text_color=self.COLOR_TEXT_LIGHT
        )
        l3.pack(anchor='w', pady=(4, 0))
        
        self._bind_mouse_wheel(row)
        self._bind_mouse_wheel(header)
        self._bind_mouse_wheel(l1)
        self._bind_mouse_wheel(l2)
        self._bind_mouse_wheel(bar)
        self._bind_mouse_wheel(l3)
        
        if not is_last:
            sep = ctk.CTkFrame(parent, height=1, fg_color="#EEEEEE")
            sep.pack(fill='x', padx=20)
            self._bind_mouse_wheel(sep)