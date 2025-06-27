import customtkinter as ctk

class ProgressView(ctk.CTkFrame):
    def __init__(self, master, stats, mastered, weak, subject_stats, next_concept, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_back = on_back
        self.label = ctk.CTkLabel(self, text="Your Progress", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 10))

        self.stats_label = ctk.CTkLabel(self, text=f"Questions Answered: {stats['total']}\nCorrect Answers: {stats['correct']}\nScore: {stats['score']:.1f}%", font=ctk.CTkFont(size=16))
        self.stats_label.pack(pady=(0, 20))

        self.mastered_label = ctk.CTkLabel(self, text="Mastered Concepts:", font=ctk.CTkFont(size=16, weight="bold"))
        self.mastered_label.pack(pady=(0, 5))
        if mastered:
            for m in mastered:
                ctk.CTkLabel(self, text=f"• {m}", font=ctk.CTkFont(size=15)).pack(anchor='w', padx=40)
        else:
            ctk.CTkLabel(self, text="None yet.", font=ctk.CTkFont(size=15)).pack(anchor='w', padx=40)

        self.weak_label = ctk.CTkLabel(self, text="\nTopics to Review:", font=ctk.CTkFont(size=16, weight="bold"))
        self.weak_label.pack(pady=(10, 5))
        if weak:
            for w in weak:
                ctk.CTkLabel(self, text=f"• {w}", font=ctk.CTkFont(size=15)).pack(anchor='w', padx=40)
        else:
            ctk.CTkLabel(self, text="None!", font=ctk.CTkFont(size=15)).pack(anchor='w', padx=40)

        # Subject-wise progress bars
        ctk.CTkLabel(self, text="\nYour Progress in Each Subject:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        for subject, stats in subject_stats.items():
            pct = stats['pct']
            bar = ctk.CTkProgressBar(self, width=300)
            bar.set(pct / 100)
            bar.pack(pady=2)
            ctk.CTkLabel(self, text=f"{subject}: {pct:.1f}%", font=ctk.CTkFont(size=14)).pack()

        # Next concept suggestion
        if next_concept:
            ctk.CTkLabel(self, text="\nReady for your next challenge?", font=ctk.CTkFont(size=16, weight="bold"), text_color="#388e3c").pack(pady=(20, 0))
            ctk.CTkLabel(self, text=next_concept, font=ctk.CTkFont(size=15), text_color="#388e3c").pack()

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(30, 0)) 