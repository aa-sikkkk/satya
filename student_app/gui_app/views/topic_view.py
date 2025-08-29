import customtkinter as ctk

class TopicView(ctk.CTkFrame):
    def __init__(self, master, topics, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.topics = topics

        # Main title
        self.label = ctk.CTkLabel(self, text="Select a Topic", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        # Create scrollable frame for topics
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=600, height=400)
        self.scrollable_frame.pack(pady=(0, 20), padx=20, fill='both', expand=True)

        # Add topic buttons to scrollable frame
        self.topic_buttons = []
        for topic in topics:
            # When receiving flattened entries, prefer 'label' for display and pass the full object back
            label = topic.get("label") if isinstance(topic, dict) and "label" in topic else (topic.get("name") if isinstance(topic, dict) else topic)
            btn = ctk.CTkButton(self.scrollable_frame, text=label, width=220, command=lambda t=topic: self.on_select(t))
            btn.pack(pady=8)
            self.topic_buttons.append(btn)

        # Back button
        self.back_btn = ctk.CTkButton(self, text="Back to Subjects", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(20, 30)) 