# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

import customtkinter as ctk
from student_app.gui_app.views import WelcomeView, GradeView, SubjectView, TopicView, ConceptView, ConceptDetailView, QuestionView, ProgressView, AskQuestionView, ProgressOpsView, AboutView, UserGuideView
from system.data_manager.content_manager import ContentManager
from system.rag.rag_retrieval_engine import RAGRetrievalEngine
from student_app.progress import progress_manager
from ai_model.model_utils.model_handler import ModelHandler
from student_app.learning.openai_proxy_client import OpenAIProxyClient
from system.utils.resource_path import resolve_model_dir, resolve_content_dir, resolve_chroma_db_dir
from student_app.gui_app.components.grade_selector import GradeSelector
from student_app.gui_app.components.subject_selector import SubjectSelector

import difflib
import re
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import os
import ctypes
import json
from PIL import Image
import threading
import atexit
import time

class NEBeduApp(ctk.CTk):
    """Main application window for Satya Learning System."""
    
    def __init__(self):
        super().__init__()
        
        try:
            myappid = 'satya.learning.companion.1.0' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
            
        self.title('Satya: Learning Companion')
        self.geometry('1200x750')
        self.minsize(900, 600)
        
        self.withdraw()
        
        ctk.set_appearance_mode('light')
        ctk.set_default_color_theme('green')
        
        self._cache = {}
        self._loading = False
        self._update_timer = None
        self._initialization_done = False
        
        self.username = None
        self.content_manager = None
        
        self.rag_engine = None
        self._rag_initialized = False
        
        self.model_handler = None
        self.model_path = None
        
        proxy_url = os.getenv("OPENAI_PROXY_URL")
        proxy_api_key = os.getenv("OPENAI_PROXY_KEY")
        self.openai_client = OpenAIProxyClient(proxy_url=proxy_url, api_key=proxy_api_key)

        atexit.register(self.cleanup_model)
        self.selected_subject = None
        self.selected_topic = None
        self.selected_concept = None
        self.selected_concept_data = None
        self.question_index = 0
        
        self.current_grade_filter = "10"
        self.current_subject_filter = "Science"
        self.selected_grade = None

        self._set_window_icon()
        self._create_ui_structure()
        self._eager_init_all_models()

    def _set_window_icon(self):
        def _apply_icon():
            try:
                logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
                
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logo.png")
                
                if os.path.exists(logo_path):
                    try:
                        ico_path = os.path.splitext(logo_path)[0] + ".ico"
                        
                        if not os.path.exists(ico_path):
                            img = Image.open(logo_path)
                            img.save(ico_path, format='ICO', sizes=[(32, 32), (64, 64), (128, 128)])
                        
                        self.iconbitmap(ico_path)
                    except Exception:
                        icon_image = Image.open(logo_path)
                        self.app_icon = ImageTk.PhotoImage(icon_image)
                        self.wm_iconphoto(True, self.app_icon)
            except Exception as e:
                print(f"Could not set window icon: {e}")
        
        self.after(200, _apply_icon)
    
    def _create_ui_structure(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill='both', expand=True)

        self.sidebar = ctk.CTkFrame(
            self.container,
            width=220,
            corner_radius=0,
            fg_color="#F5F5F5"
        )
        self.sidebar.grid(row=0, column=0, sticky='ns')
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_remove()

        self._create_sidebar()

        self.main_content = ctk.CTkFrame(
            self.container,
            corner_radius=0,
            fg_color="#FFFFFF"
        )
        self.main_content.grid(row=0, column=1, sticky='nsew', padx=0, pady=0)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(
            self.main_content,
            height=60,
            corner_radius=0,
            fg_color="#FFFFFF",
            border_width=0,
            border_color="#E0E0E0"
        )
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)

        self.sidebar_toggle_btn = ctk.CTkButton(
            self.top_bar,
            text="☰",
            width=40,
            height=40,
            corner_radius=8,
            command=self.toggle_sidebar,
            fg_color="#E8F5E9",
            hover_color="#C8E6C9",
            text_color="#2E7D32"
        )
        self.sidebar_toggle_btn.pack(side="left", padx=15, pady=10)
        
        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="Satya Learning System",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2E7D32"
        )
        self.title_label.pack(side="left", padx=15)
        
        self.grade_selector = GradeSelector(self.top_bar, command=self.on_grade_change, width=120)
        self.grade_selector.pack(side="right", padx=5)

        self.subject_selector = SubjectSelector(self.top_bar, command=self.on_subject_change, width=140)
        self.subject_selector.pack(side="right", padx=5)
        
        self.current_subject_filter = self.subject_selector.get()
        self.current_grade_filter = str(int(self.grade_selector.get().split()[-1]))

        self.sidebar_shown = False

        self.main_frame = ctk.CTkFrame(
            self.main_content,
            corner_radius=0,
            fg_color="#FAFAFA"
        )
        self.main_frame.pack(side="bottom", fill="both", expand=True, padx=0, pady=0)

        self.welcome_view = WelcomeView(self.main_frame, self.on_login)
        self.welcome_view.pack(fill='both', expand=True)

    def on_grade_change(self, value):
        try:
            self.current_grade_filter = str(int(value.split()[-1]))
            self.selected_grade = int(self.current_grade_filter)
        except Exception:
            pass

    def on_subject_change(self, value):
        self.current_subject_filter = value
        self.selected_subject = value

    def _create_sidebar(self):
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(25, 20), fill="x")
        
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            if os.path.exists(logo_path):
                logo_img = ctk.CTkImage(light_image=Image.open(logo_path), size=(100, 100))
                self.logo_image_label = ctk.CTkLabel(logo_frame, image=logo_img, text="")
                self.logo_image_label.pack()
            else:
                ctk.CTkLabel(
                    logo_frame,
                    text="🌟 Satya",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color="#2E7D32"
                ).pack()
        except Exception:
            ctk.CTkLabel(
                logo_frame,
                text="🌟 Satya",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#2E7D32"
            ).pack()

        nav_buttons = [
            ('📚 Browse Subjects', self.show_browse, "#2E7D32"),
            ('❓ Ask Question', self.show_ask, "#1976D2"),
            ('📊 Progress', self.show_progress, "#7B1FA2"),
            ('⚙️ Progress Ops', self.show_progress_ops, "#F57C00"),
            ('ℹ️ About', self.show_about, "#616161"),
            ('📘 User Guide', self.show_user_guide, "#00796B"),
        ]
        
        for text, command, color in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                height=45,
                font=ctk.CTkFont(size=15, weight="normal"),
                corner_radius=10,
                fg_color=color,
                hover_color=self._darken_color(color),
                anchor="w"
            )
            btn.pack(pady=8, fill='x', padx=15)

        self.btn_exit = ctk.CTkButton(
            self.sidebar,
            text='🚪 Exit',
            command=self.quit,
            height=45,
            font=ctk.CTkFont(size=15, weight="normal"),
            corner_radius=10,
            fg_color='#E53935',
            hover_color='#C62828',
            anchor="w"
        )
        self.btn_exit.pack(pady=(30, 0), fill='x', padx=15)

        self.model_info_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="#E8F5E9",
            corner_radius=10
        )
        self.model_info_frame.pack(side="bottom", pady=15, padx=15, fill="x")
        
        self.model_info_label = ctk.CTkLabel(
            self.model_info_frame,
            text="Initializing...",
            font=ctk.CTkFont(size=11),
            text_color="#424242",
            wraplength=180
        )
        self.model_info_label.pack(pady=10, padx=10)

    def _darken_color(self, hex_color):
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        r = max(0, int(hex_color[0:2], 16) - 30)
        g = max(0, int(hex_color[2:4], 16) - 30)
        b = max(0, int(hex_color[4:6], 16) - 30)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _eager_init_all_models(self):
        from student_app.gui_app.startup_loader import StartupLoader
        
        loader = StartupLoader() 
        loader.update()
        loader.update_idletasks()
        
        try:
            loader.update_status("Loading content...", "Initializing content manager", 0.1)
            loader.update_idletasks()
            self.content_manager = ContentManager()
            
            loader.update_status("Locating model...", "Finding Phi 1.5 model files", 0.2)
            loader.update_idletasks()
            self.model_path = str(resolve_model_dir("satya_data/models/phi15"))
            
            loader.update_status("Loading Phi 1.5...", "Loading and warming up model", 0.3)
            loader.update_idletasks()
            self.model_handler = ModelHandler(self.model_path)
            
            loader.update_status("Loading RAG Engine...", "Initializing embeddings and database", 0.6)
            loader.update_idletasks()
            chroma_db_path = str(resolve_model_dir("satya_data/chroma_db"))
            self.rag_engine = RAGRetrievalEngine(
                chroma_db_path=chroma_db_path,
                llm_handler=self.model_handler
            )
            
            loader.update_status("Warming up RAG...", "Pre-loading embeddings and database", 0.8)
            loader.update_idletasks()
            self.rag_engine.warm_up()  
            self._rag_initialized = True
            
            loader.update_status("Ready!", "All systems loaded and ready", 1.0)
            loader.update_idletasks()
            time.sleep(0.5)
            
            self._update_model_info()
            self._update_status("Ready!")
            self._initialization_done = True
            
            loader.destroy()
            self.deiconify()
            self.update()
            
        except Exception as e:
            loader.destroy()
            self._show_model_error(f"Initialization error: {e}")
            self.deiconify()
            self.update()

    def _update_status(self, message):
        if hasattr(self, 'model_info_label'):
            self.model_info_label.configure(text=message)
    
    def _update_model_info(self):
        try:
            if self.model_handler:
                model_info = self.model_handler.get_model_info()
                if model_info:
                    info_text = f"🤖 {model_info.get('name', 'AI Model')}\n"
                    info_text += f"Context: {model_info.get('context_size', 'N/A')}"
                    self.model_info_label.configure(text=info_text)
        except Exception:
            self.model_info_label.configure(text="Model loaded")
    
    def _show_model_error(self, error_msg):
        self.model_info_label.configure(
            text=f"⚠️ Error: {error_msg[:50]}...",
            text_color="#E53935"
        )

    def toggle_sidebar(self):
        if self.sidebar_shown:
            self.sidebar.grid_remove()
            self.sidebar_shown = False
        else:
            self.sidebar.grid()
            self.sidebar_shown = True

    def cleanup_model(self):
        try:
            if hasattr(self.model_handler, 'bitnet_handler'):
                self.model_handler.bitnet_handler.cleanup()
        except Exception:
            pass
            
    def _lazy_init_rag(self):
        if not self._rag_initialized:
            try:
                chroma_db_path = str(resolve_chroma_db_dir("satya_data/chroma_db"))
                self.rag_engine = RAGRetrievalEngine(chroma_db_path=chroma_db_path)
                self._rag_initialized = True
            except Exception as e:
                self.rag_engine = None
                self._rag_initialized = True

    def _debounced_update(self, func, delay=50):
        if self._update_timer:
            self.after_cancel(self._update_timer)
        self._update_timer = self.after(delay, func)

    def _safe_destroy_widgets(self):
        try:
            for widget in self.main_frame.winfo_children():
                widget.destroy()
        except Exception:
            pass

    def on_login(self, username):
        self.username = username
        self.welcome_view.pack_forget()
        self.sidebar.grid()
        self.sidebar_shown = True
        self.show_main_menu()
    
    def show_main_menu(self):
        if self._loading: return
        self._safe_destroy_widgets()
        dashboard_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        dashboard_frame.pack(fill='both', expand=True, padx=40, pady=40)
        welcome_header = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        welcome_header.pack(fill='x', pady=(0, 30))
        welcome_title = ctk.CTkLabel(welcome_header, text=f"Welcome back, {self.username}! 👋", font=ctk.CTkFont(size=36, weight="bold"), text_color="#2E7D32")
        welcome_title.pack(anchor='w')
        welcome_subtitle = ctk.CTkLabel(welcome_header, text="Your personal learning dashboard", font=ctk.CTkFont(size=18), text_color="#666666")
        welcome_subtitle.pack(anchor='w', pady=(5, 0))
        features_frame = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        features_frame.pack(fill='both', expand=True)
        features = [("📚", "Browse Subjects", "Explore a wide range of subjects and topics", self.show_browse, "#2E7D32"), ("❓", "Ask Questions", "Get instant answers from our AI assistant", self.show_ask, "#1976D2"), ("📊", "Track Progress", "See how you're doing and where to improve", self.show_progress, "#7B1FA2")]
        for icon, title, desc, command, color in features:
            card = ctk.CTkFrame(features_frame, corner_radius=15, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
            card.pack(side='left', fill='both', expand=True, padx=10, pady=10)
            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=48))
            icon_label.pack(pady=(20, 10))
            title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
            title_label.pack(pady=(0, 10))
            desc_label = ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=14), text_color="#666666", wraplength=200, justify='center')
            desc_label.pack(pady=(0, 20), padx=20)
            action_btn = ctk.CTkButton(card, text="Get Started", command=command, fg_color=color, hover_color=self._darken_color(color), width=150, height=35)
            action_btn.pack(pady=(0, 20))

    def show_browse(self):
        """Show grade selection first, then proceed to subjects."""
        if self._loading: return
        self._safe_destroy_widgets()
        
        view = GradeView(
            self.main_frame, 
            on_select=self.on_grade_selected, 
            on_back=self.show_main_menu
        )
        view.pack(fill='both', expand=True)
    
    def on_grade_selected(self, grade: int):
        """Handle grade selection, then show subjects."""
        self.current_grade_filter = str(grade)
        self.selected_grade = grade
        
        if hasattr(self, 'grade_selector'):
            self.grade_selector.set(f"Grade {grade}")
        
        if not self.content_manager:
            self._show_loading_message("Initializing... Please wait.")
            self.after(100, lambda: self.on_grade_selected(grade))
            return
        
        self._loading = True
        self._safe_destroy_widgets()
        
        loading_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        loading_frame.pack(fill='both', expand=True)
        loading_icon = ctk.CTkLabel(loading_frame, text="⏳", font=ctk.CTkFont(size=48))
        loading_icon.pack(pady=40)
        loading_label = ctk.CTkLabel(loading_frame, text="Loading subjects...", font=ctk.CTkFont(size=18), text_color="#666666")
        loading_label.pack(pady=10)
        self.update()
        
        def load_subjects():
            try:
                subjects = self.content_manager.get_all_subjects()
                def show_subjects():
                    self._safe_destroy_widgets()
                    view = SubjectView(self.main_frame, subjects, self.on_subject_selected, self.show_browse)
                    view.pack(fill='both', expand=True)
                    self._loading = False
                self.after(0, show_subjects)
            except Exception as e:
                def show_error():
                    self._safe_destroy_widgets()
                    mb.showerror("Error", f"Failed to load subjects: {e}")
                    self.show_main_menu()
                    self._loading = False
                self.after(0, show_error)
        threading.Thread(target=load_subjects, daemon=True).start()


    def _show_loading_message(self, message):
         self._safe_destroy_widgets()
         loading_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
         loading_frame.pack(fill='both', expand=True)
         ctk.CTkLabel(loading_frame, text=message, font=ctk.CTkFont(size=16), text_color="#666666").pack(pady=40)

    def on_subject_selected(self, subject):
        if self._loading: return
        self._loading = True
        self.selected_subject = subject
        self.subject_selector.set(subject)
        self.current_subject_filter = subject
        self._safe_destroy_widgets()
        loading = ctk.CTkLabel(self.main_frame, text="Loading topics...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        def load_topics():
            try:
                topics = self.content_manager.list_browseable_topics(subject)
                def show_topics():
                    self._safe_destroy_widgets()
                    view = TopicView(self.main_frame, topics, self.on_topic_selected, self.show_browse)
                    view.pack(fill='both', expand=True)
                    self._loading = False
                self.after(0, show_topics)
            except Exception as e:
                 def show_error():
                    self._safe_destroy_widgets()
                    mb.showerror("Error", f"Failed to load topics: {e}")
                    self.show_browse()
                    self._loading = False
                 self.after(0, show_error)
        threading.Thread(target=load_topics, daemon=True).start()

    def on_topic_selected(self, topic):
        if self._loading: return
        self._loading = True
        if isinstance(topic, dict) and "topic" in topic:
            self.selected_topic = topic["topic"]
            self.selected_subtopic_path = topic.get("subtopic_path", [])
            display_label = topic.get("label", self.selected_topic)
        else:
            self.selected_topic = topic.get("name") if isinstance(topic, dict) else topic
            self.selected_subtopic_path = []
            display_label = self.selected_topic
        self._safe_destroy_widgets()
        loading = ctk.CTkLabel(self.main_frame, text=f"Loading concepts for {display_label}...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        def load_concepts():
            try:
                concepts = self.content_manager.get_concepts_at_path(self.selected_subject, self.selected_topic, self.selected_subtopic_path,)
                def show_concepts():
                    self._safe_destroy_widgets()
                    view = ConceptView(self.main_frame, concepts, self.on_concept_selected, lambda: self.on_subject_selected(self.selected_subject))
                    view.pack(fill='both', expand=True)
                    self._loading = False
                self.after(0, show_concepts)
            except Exception as e:
                def show_error():
                    self._safe_destroy_widgets()
                    mb.showerror("Error", f"Failed to load concepts: {e}")
                    self.on_subject_selected(self.selected_subject)
                    self._loading = False
                self.after(0, show_error)
        threading.Thread(target=load_concepts, daemon=True).start()

    def on_concept_selected(self, concept_name):
        if self._loading: return
        self._loading = True
        self.selected_concept = concept_name
        self._safe_destroy_widgets()
        loading = ctk.CTkLabel(self.main_frame, text="Loading concept details...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        def load_concept():
            try:
                concept = self.content_manager.get_concept(self.selected_subject, self.selected_topic, concept_name)
                self.selected_concept_data = concept
                def show_concept():
                    self._safe_destroy_widgets()
                    view = ConceptDetailView(self.main_frame, concept, self.start_questions, lambda: self.on_topic_selected(self.selected_topic))
                    view.pack(fill='both', expand=True)
                    self._loading = False
                self.after(0, show_concept)
            except Exception as e:
                def show_error():
                    self._safe_destroy_widgets()
                    mb.showerror("Error", f"Failed to load concept: {e}")
                    self.on_topic_selected(self.selected_topic)
                    self._loading = False
                self.after(0, show_error)
        threading.Thread(target=load_concept, daemon=True).start()

    def start_questions(self):
        self.question_index = 0
        self.show_question()

    def show_question(self):
        if self._loading: return
        self._loading = True
        concept = self.selected_concept_data
        questions = concept.get('questions', [])
        if self.question_index >= len(questions):
            self.show_concept_complete()
            return
        q = questions[self.question_index]
        self._safe_destroy_widgets()
        view = QuestionView(self.main_frame, q['question'], lambda ans: self.on_answer_submitted(ans, q), lambda: self.on_concept_selected(self.selected_concept))
        view.pack(fill='both', expand=True)
        self._loading = False

    def on_answer_submitted(self, answer, question):
        if self._loading: return
        self._loading = True
        
        self._safe_destroy_widgets()
        loading = ctk.CTkLabel(self.main_frame, text="🤖 AI is grading your answer...", font=ctk.CTkFont(size=18))
        loading.pack(pady=40)
        
        def worker():
            user_ans = answer.strip()
            correct_ans = question.get('answer', '').strip()
            
            is_correct, explanation = self._grade_answer_with_ai(question['question'], user_ans, correct_ans)
            
            def show_result():
                progress_manager.update_progress(self.username, self.selected_subject, self.selected_topic, self.selected_concept, question['question'], is_correct)
                
                self._safe_destroy_widgets()
                if is_correct:
                    msg = "✅ Correct!"
                    color = "#43a047"
                else:
                    msg = "❌ Incorrect"
                    color = "#e53935"
                
                result_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
                result_frame.pack(fill='both', expand=True, pady=40)
                
                label = ctk.CTkLabel(result_frame, text=msg, font=ctk.CTkFont(size=22, weight="bold"), text_color=color, wraplength=600)
                label.pack(pady=(40, 10))
                
                exp_text = explanation if explanation else question.get('explanation', f"The correct answer is: {correct_ans}")
                
                exp_frame = ctk.CTkFrame(result_frame, fg_color="#f5f5f5", corner_radius=10)
                exp_frame.pack(pady=20, padx=40, fill='x')
                ctk.CTkLabel(exp_frame, text="Feedback:", font=ctk.CTkFont(size=16, weight="bold"), text_color="#424242").pack(anchor='w', padx=15, pady=(10, 5))
                ctk.CTkLabel(exp_frame, text=exp_text, font=ctk.CTkFont(size=14), text_color="#616161", wraplength=500, justify='left').pack(anchor='w', padx=15, pady=(0, 10))
                
                ctk.CTkButton(result_frame, text="Next Question", command=self.next_question, width=200, height=40).pack(pady=30)
                self._loading = False
                
            self.after(0, show_result)
            
        threading.Thread(target=worker, daemon=True).start()

    def next_question(self):
        if self._loading: return
        self.question_index += 1
        self.show_question()

    def show_concept_complete(self):
        if self._loading: return
        self._loading = True
        self._safe_destroy_widgets()
        complete_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        complete_frame.pack(fill='both', expand=True, pady=60)
        ctk.CTkLabel(complete_frame, text="🎉 Congratulations!", font=ctk.CTkFont(size=32, weight="bold"), text_color="#2E7D32").pack(pady=(40, 10))
        ctk.CTkLabel(complete_frame, text="You've completed all questions for this concept!", font=ctk.CTkFont(size=18), text_color="#666666").pack(pady=10)
        ctk.CTkButton(complete_frame, text="Back to Concepts", command=lambda: self.on_topic_selected(self.selected_topic), width=200, height=40).pack(pady=30)
        self._loading = False

    def show_ask(self):
        if self._loading: return
        self._loading = True
        self._safe_destroy_widgets()
        self.ask_view = AskQuestionView(self.main_frame, self.on_ask_submit, self.show_main_menu, self.on_ask_openai)
        self.ask_view.pack(fill='both', expand=True)
        self._loading = False

    def on_ask_openai(self, question):
        if self._loading: return
        self._loading = True
        self.ask_view.set_loading(True)
        def worker():
            try:
                answer = self.openai_client.ask(question, user_id=self.username)
                def show_result():
                    self.ask_view.set_result(answer, is_openai=True)
                    self._loading = False
                self.after(0, show_result)
            except Exception as e:
                def show_error():
                    mb.showerror("OpenAI Error", f"Failed to get answer from OpenAI: {e}")
                    self.ask_view.set_loading(False)
                    self._loading = False
                self.after(0, show_error)
        threading.Thread(target=worker, daemon=True).start()

    
    def _grade_answer_with_ai(self, question_text, user_answer, correct_answer):
        """Using the model to grade the answer relative to the correct answer."""
        if not self.model_handler:
            is_correct = (user_answer.lower() == correct_answer.lower()) or (difflib.SequenceMatcher(None, user_answer.lower(), correct_answer.lower()).ratio() > 0.8)
            return is_correct, f"The correct answer is: {correct_answer}"

        prompt = (
            f"Task: Grade the student's answer based on the Correct Answer. Provide helpful, specific feedback.\n\n"
            f"Example 1:\n"
            f"Question: What is the function of mitochondria?\n"
            f"Correct Answer: It generates energy for the cell through respiration.\n"
            f"Student Answer: It protects the nucleus.\n"
            f"Verdict: [INCORRECT]\n"
            f"Feedback: That is incorrect. The nucleus is protected by the nuclear membrane. Mitochondria are the 'powerhouse' of the cell responsible for generating energy (ATP).\n\n"
            f"Example 2:\n"
            f"Question: What is 2 + 2?\n"
            f"Correct Answer: 4\n"
            f"Student Answer: It is four.\n"
            f"Verdict: [CORRECT]\n"
            f"Feedback: Correct! You identified the right number.\n\n"
            f"Current Task:\n"
            f"Question: {question_text}\n"
            f"Correct Answer: {correct_answer}\n"
            f"Student Answer: {user_answer}\n"
            f"Verdict:"
        )
        
        try:

            response = self.model_handler.generate_response(prompt, max_tokens=100)
            
            response_upper = response.upper()
            is_correct = "[CORRECT]" in response_upper
            explanation = response
            
            explanation = re.sub(r'^\[.*?\]', '', explanation).strip()
            
            if explanation.upper().startswith("VERDICT:"):
                explanation = explanation[8:].strip()
                explanation = re.sub(r'^\[.*?\]', '', explanation).strip()
                
            if explanation.upper().startswith("FEEDBACK:"):
                explanation = explanation[9:].strip()
            
            explanation = explanation.strip()
            
            if not is_correct and "[INCORRECT]" not in response_upper:
                 
                 is_correct = (user_answer.lower() == correct_answer.lower())
            
            return is_correct, explanation
            
        except Exception as e:
            print(f"AI Grading Error: {e}")
            is_correct = (user_answer.lower() == correct_answer.lower()) or (difflib.SequenceMatcher(None, user_answer.lower(), correct_answer.lower()).ratio() > 0.8)
            return is_correct, f"The correct answer is: {correct_answer}"

    def on_ask_submit(self, question, answer_length="medium"):
        if self._loading:
            return
        self._loading = True
        
        self.ask_view.set_loading(True)
        
        def worker():
            try:
                normalized_question = question.strip()
                if not normalized_question:
                    def show_error():
                        mb.showerror("Error", "Please enter a question")
                        self.ask_view.set_loading(False)
                        self._loading = False
                    self.after(0, show_error)
                    return
                
                if not self.rag_engine:
                    def show_error():
                        self.ask_view.set_result(
                            "RAG Engine not initialized. Please restart the app.",
                            is_openai=False
                        )
                        self._loading = False
                    self.after(0, show_error)
                    return
                
                first_token = [True]
                
                def on_token(token):
                    print(f"GUI: Received token: '{token}'", flush=True)
                    def display():
                        if first_token[0]:
                            self.ask_view.set_loading(False)
                            first_token[0] = False
                        self.ask_view.append_answer_token(token)
                    self.after(0, display)
                
                try:
                    response = self.rag_engine.query(
                        query_text=normalized_question,
                        subject=self.current_subject_filter,
                        stream_callback=on_token
                    )
                    
                    confidence = response.get('confidence', 0.5)
                    diagram = response.get('diagram')
                    
                    def finalize():
                        self.ask_view.finalize_answer(
                            confidence, 
                            question=normalized_question,
                            grade=self.selected_grade,
                            subject=self.current_subject_filter
                        )
                        
                        if diagram:
                            try:
                                self.ask_view.show_diagram(diagram)
                            except AttributeError:
                                pass
                        
                        self._loading = False
                    
                    self.after(0, finalize)
                    
                except Exception as e:
                    error_msg = str(e)
                    def show_error():
                        mb.showerror("RAG Error", f"Failed to get answer: {error_msg}")
                        self.ask_view.set_loading(False)
                        self._loading = False
                    self.after(0, show_error)
                    
            except Exception as ex:
                error_msg = str(ex)
                def show_error():
                    mb.showerror("Error", f"An error occurred: {error_msg}")
                    self.ask_view.set_loading(False)
                    self._loading = False
                self.after(0, show_error)
        
        threading.Thread(target=worker, daemon=True).start()

    def _calculate_progress_stats(self):
        progress_data = progress_manager.load_progress(self.username)
        
        total_q = 0
        total_correct = 0
        mastered = []
        weak = []
        subject_stats = {}
        
        for subject, topics in progress_data.items():
            subj_total = 0
            subj_correct = 0
            
            for topic, concepts in topics.items():
                for concept, data in concepts.items():
                    questions = data.get('questions', [])
                    c_total = sum(q['attempts'] for q in questions)
                    c_correct = sum(q['correct'] for q in questions)
                    
                    if c_total >= 5:
                        score = (c_correct / c_total) * 100
                        if score >= 80:
                            mastered.append(f"{concept} ({topic})")
                        elif score < 50:
                            weak.append(f"{concept} ({topic})")
                    
                    subj_total += c_total
                    subj_correct += c_correct
            
            if subj_total > 0:
                pct = (subj_correct / subj_total) * 100
                subject_stats[subject] = {
                    'pct': pct,
                    'correct': subj_correct,
                    'total': subj_total
                }
            
            total_q += subj_total
            total_correct += subj_correct
            
        overall_score = (total_correct / total_q * 100) if total_q > 0 else 0
        
        stats = {
            'total': total_q,
            'correct': total_correct,
            'score': overall_score
        }
        
        next_concept = None
        if weak:
            next_concept = f"Try reviewing: {weak[0]}"
        elif mastered:
             next_concept = "Great work! Try exploring a new subject."
        else:
             next_concept = "Start by browsing subjects to begin your journey!"

        return stats, mastered, weak, subject_stats, next_concept

    def _export_progress(self):
        src = progress_manager.get_progress_path(self.username)
        if not os.path.exists(src):
            mb.showinfo("Info", "No progress data to export.")
            return
            
        dest = fd.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"satya_progress_{self.username}.json",
            title="Export Progress"
        )
        if dest:
            import shutil
            try:
                shutil.copy2(src, dest)
                mb.showinfo("Success", "Progress exported successfully!")
            except Exception as e:
                mb.showerror("Error", f"Failed to export: {e}")

    def _import_progress(self):
        src = fd.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Import Progress"
        )
        if src:
            dest = progress_manager.get_progress_path(self.username)
            import shutil
            try:
                shutil.copy2(src, dest)
                mb.showinfo("Success", "Progress imported successfully! Please restart to see changes.")
                self.show_progress_ops()
            except Exception as e:
                mb.showerror("Error", f"Failed to import: {e}")

    def _reset_progress(self):
        if mb.askyesno("Confirm Reset", "Are you sure you want to delete all progress? This cannot be undone."):
            try:
                path = progress_manager.get_progress_path(self.username)
                if os.path.exists(path):
                    os.remove(path)
                mb.showinfo("Success", "Progress has been reset.")
                self.show_progress_ops()
            except Exception as e:
                mb.showerror("Error", f"Failed to reset: {e}")

    def show_progress(self):
        if self._loading: return
        self._loading = True
        self._safe_destroy_widgets()
        
        stats, mastered, weak, subject_stats, next_concept = self._calculate_progress_stats()
        
        view = ProgressView(
            self.main_frame, 
            stats=stats,
            mastered=mastered,
            weak=weak,
            subject_stats=subject_stats,
            next_concept=next_concept, 
            on_back=self.show_main_menu
        )
        view.pack(fill='both', expand=True)
        self._loading = False

    def show_progress_ops(self):
        if self._loading: return
        self._loading = True
        self._safe_destroy_widgets()
        
        view = ProgressOpsView(
            self.main_frame, 
            on_export=self._export_progress,
            on_import=self._import_progress,
            on_reset=self._reset_progress,
            on_back=self.show_main_menu
        )
        view.pack(fill='both', expand=True)
        self._loading = False

    def show_user_guide(self):
        if self._loading: return
        self._loading = True
        self._safe_destroy_widgets()
        view = UserGuideView(self.main_frame, self.show_main_menu)
        view.pack(fill='both', expand=True)
        self._loading = False

    def show_about(self):
        if self._loading: return
        self._loading = True
        self._safe_destroy_widgets()
        view = AboutView(self.main_frame, self.show_main_menu)
        view.pack(fill='both', expand=True)
        self._loading = False

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    app = NEBeduApp()
    app.mainloop()