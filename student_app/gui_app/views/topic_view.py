import customtkinter as ctk

class TopicView(ctk.CTkFrame):
    def __init__(self, master, topics, on_select, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_select = on_select
        self.on_back = on_back
        self.topics = topics

        self.label = ctk.CTkLabel(self, text="Select a Topic", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        self.topic_buttons = []
        for topic in topics:
            btn = ctk.CTkButton(self, text=topic, width=220, command=lambda t=topic: self.on_select(t))
            btn.pack(pady=8)
            self.topic_buttons.append(btn)

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(40, 0)) 