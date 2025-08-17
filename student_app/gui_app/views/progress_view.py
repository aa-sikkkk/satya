import customtkinter as ctk

class ProgressView(ctk.CTkFrame):
    def __init__(self, master, stats, mastered, weak, subject_stats, next_concept, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_back = on_back
        
        # Main title
        self.label = ctk.CTkLabel(self, text="Your Progress", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        # Create scrollable frame for all content
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=700, height=500)
        self.scrollable_frame.pack(pady=(0, 20), padx=20, fill='both', expand=True)

        # Overall stats section
        stats_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#e8f5e8", corner_radius=8)
        stats_frame.pack(pady=(0, 15), padx=10, fill='x')
        
        ctk.CTkLabel(stats_frame, text="📊 Overall Performance", font=ctk.CTkFont(size=16, weight="bold"), text_color="#388e3c").pack(pady=(10, 5), padx=10, anchor='w')
        self.stats_label = ctk.CTkLabel(stats_frame, text=f"Questions Answered: {stats['total']}\nCorrect Answers: {stats['correct']}\nScore: {stats['score']:.1f}%", font=ctk.CTkFont(size=16))
        self.stats_label.pack(pady=(0, 10), padx=10, anchor='w')

        # Mastered concepts section
        mastered_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#fff3e0", corner_radius=8)
        mastered_frame.pack(pady=(0, 15), padx=10, fill='x')
        
        ctk.CTkLabel(mastered_frame, text="🏆 Mastered Concepts", font=ctk.CTkFont(size=16, weight="bold"), text_color="#f57c00").pack(pady=(10, 5), padx=10, anchor='w')
        if mastered:
            for m in mastered:
                ctk.CTkLabel(mastered_frame, text=f"• {m}", font=ctk.CTkFont(size=14), wraplength=600, justify='left').pack(anchor='w', padx=20, pady=2)
        else:
            ctk.CTkLabel(mastered_frame, text="None yet. Keep studying!", font=ctk.CTkFont(size=14), text_color="#757575").pack(anchor='w', padx=20, pady=5)

        # Weak areas section
        weak_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#ffebee", corner_radius=8)
        weak_frame.pack(pady=(0, 15), padx=10, fill='x')
        
        ctk.CTkLabel(weak_frame, text="📚 Topics to Review", font=ctk.CTkFont(size=16, weight="bold"), text_color="#d32f2f").pack(pady=(10, 5), padx=10, anchor='w')
        if weak:
            for w in weak:
                ctk.CTkLabel(weak_frame, text=f"• {w}", font=ctk.CTkFont(size=14), wraplength=600, justify='left').pack(anchor='w', padx=20, pady=2)
        else:
            ctk.CTkLabel(weak_frame, text="Great job! No weak areas found.", font=ctk.CTkFont(size=14), text_color="#388e3c").pack(anchor='w', padx=20, pady=5)

        # Subject-wise progress section
        subject_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#f3e5f5", corner_radius=8)
        subject_frame.pack(pady=(0, 15), padx=10, fill='x')
        
        ctk.CTkLabel(subject_frame, text="📈 Subject-wise Progress", font=ctk.CTkFont(size=16, weight="bold"), text_color="#7b1fa2").pack(pady=(10, 5), padx=10, anchor='w')
        
        for subject, stats in subject_stats.items():
            subject_item_frame = ctk.CTkFrame(subject_frame, fg_color="transparent")
            subject_item_frame.pack(pady=5, padx=10, fill='x')
            
            # Subject name and percentage
            ctk.CTkLabel(subject_item_frame, text=f"{subject}: {stats['pct']:.1f}%", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(0, 2))
            
            # Progress bar
            bar = ctk.CTkProgressBar(subject_item_frame, width=400, height=8)
            bar.set(stats['pct'] / 100)
            bar.pack(anchor='w', pady=(0, 5))
            
            # Progress details
            ctk.CTkLabel(subject_item_frame, text=f"  {stats['correct']}/{stats['total']} questions correct", font=ctk.CTkFont(size=12), text_color="#757575").pack(anchor='w')

        # Next concept suggestion
        if next_concept:
            next_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#e8f5e8", corner_radius=8)
            next_frame.pack(pady=(0, 15), padx=10, fill='x')
            
            ctk.CTkLabel(next_frame, text="🚀 Ready for your next challenge?", font=ctk.CTkFont(size=16, weight="bold"), text_color="#388e3c").pack(pady=(10, 5), padx=10, anchor='w')
            ctk.CTkLabel(next_frame, text=next_concept, font=ctk.CTkFont(size=15), text_color="#388e3c", wraplength=600, justify='left').pack(pady=(0, 10), padx=10, anchor='w')

        # Back button
        self.back_btn = ctk.CTkButton(self, text="Back to Main Menu", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(20, 30)) 