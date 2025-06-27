import customtkinter as ctk

class ProgressOpsView(ctk.CTkFrame):
    def __init__(self, master, on_export, on_import, on_reset, on_back, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_export = on_export
        self.on_import = on_import
        self.on_reset = on_reset
        self.on_back = on_back

        self.label = ctk.CTkLabel(self, text="Progress Operations", font=ctk.CTkFont(size=22, weight="bold"))
        self.label.pack(pady=(30, 20))

        self.export_btn = ctk.CTkButton(self, text="Export Progress", command=self.on_export)
        self.export_btn.pack(pady=10, fill='x', padx=40)
        self.import_btn = ctk.CTkButton(self, text="Import Progress", command=self.on_import)
        self.import_btn.pack(pady=10, fill='x', padx=40)
        self.reset_btn = ctk.CTkButton(self, text="Reset Progress", fg_color="#e57373", hover_color="#ef5350", command=self.on_reset)
        self.reset_btn.pack(pady=20, fill='x', padx=40)

        self.back_btn = ctk.CTkButton(self, text="Back", command=self.on_back, fg_color="#bdbdbd", hover_color="#757575")
        self.back_btn.pack(pady=(30, 0)) 