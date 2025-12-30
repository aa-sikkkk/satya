import customtkinter as ctk
from student_app.gui_app.views import WelcomeView, SubjectView, TopicView, ConceptView, ConceptDetailView, QuestionView, ProgressView, AskQuestionView, ProgressOpsView, AboutView
from system.data_manager.content_manager import ContentManager
from system.rag.rag_retrieval_engine import RAGRetrievalEngine
from student_app.progress import progress_manager
from ai_model.model_utils.model_handler import ModelHandler
from student_app.learning.openai_proxy_client import OpenAIProxyClient
from system.utils.resource_path import resolve_model_dir, resolve_content_dir, resolve_chroma_db_dir
import difflib
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import os
import json
from PIL import Image
import threading
import atexit
import time

class NEBeduApp(ctk.CTk):
    """
    Main application window for Satya Learning System.
    
    Provides a responsive, modern GUI with non-blocking operations.
    """
    
    def __init__(self):
        super().__init__()
        self.title('Satya: Learning Companion')
        self.geometry('1200x750')
        self.minsize(900, 600)
        
        # Modern appearance settings
        ctk.set_appearance_mode('light')
        ctk.set_default_color_theme('green')
        
        # Performance optimizations
        self._cache = {}  # Widget and data caching
        self._loading = False  # Prevent multiple simultaneous operations
        self._update_timer = None  # Debounced updates
        self._initialization_done = False
        
        self.username = None
        self.content_manager = None  # Will be initialized in background
        
        # Initialize RAG system (lazy)
        self.rag_engine = None
        self._rag_initialized = False
        
        # Model handler (will be initialized in background)
        self.model_handler = None
        self.model_path = None
        
        # Configure OpenAI proxy client
        proxy_url = os.getenv("OPENAI_PROXY_URL")
        proxy_api_key = os.getenv("OPENAI_PROXY_KEY")
        self.openai_client = OpenAIProxyClient(proxy_url=proxy_url, api_key=proxy_api_key)

        atexit.register(self.cleanup_model)
        self.selected_subject = None
        self.selected_topic = None
        self.selected_concept = None
        self.selected_concept_data = None
        self.question_index = 0

        # Create UI structure first (non-blocking)
        self._create_ui_structure()
        
        # Initialize heavy components in background
        self._initialize_in_background()
    
    def _create_ui_structure(self):
        """Create the UI structure without blocking operations."""
        # Main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill='both', expand=True)

        # Sidebar (hidden until login)
        self.sidebar = ctk.CTkFrame(
            self.container,
            width=220,
            corner_radius=0,
            fg_color="#F5F5F5"
        )
        self.sidebar.grid(row=0, column=0, sticky='ns')
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_remove()

        # Sidebar content
        self._create_sidebar()

        # Main content area
        self.main_content = ctk.CTkFrame(
            self.container,
            corner_radius=0,
            fg_color="#FFFFFF"
        )
        self.main_content.grid(row=0, column=1, sticky='nsew', padx=0, pady=0)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)

        # Top bar with modern design
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

        self.sidebar_shown = False

        # Main frame for views
        self.main_frame = ctk.CTkFrame(
            self.main_content,
            corner_radius=0,
            fg_color="#FAFAFA"
        )
        self.main_frame.pack(side="bottom", fill="both", expand=True, padx=0, pady=0)

        # Start with WelcomeView
        self.welcome_view = WelcomeView(self.main_frame, self.on_login)
        self.welcome_view.pack(fill='both', expand=True)
    
    def _create_sidebar(self):
        """Create the sidebar with modern design."""
        # Logo/Title at top
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(25, 20), fill="x")
        
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            if os.path.exists(logo_path):
                logo_img = ctk.CTkImage(light_image=Image.open(logo_path), size=(100, 100))
                self.logo_image_label = ctk.CTkLabel(logo_frame, image=logo_img, text="")
                self.logo_image_label.pack()
            else:
                # Fallback text logo
                ctk.CTkLabel(
                    logo_frame,
                    text="🌟 Satya",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color="#2E7D32"
                ).pack()
        except Exception:
            # Fallback text logo
            ctk.CTkLabel(
                logo_frame,
                text="🌟 Satya",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#2E7D32"
            ).pack()

        # Navigation buttons with modern styling
        nav_buttons = [
            ('📚 Browse Subjects', self.show_browse, "#2E7D32"),
            ('❓ Ask Question', self.show_ask, "#1976D2"),
            ('📊 Progress', self.show_progress, "#7B1FA2"),
            ('⚙️ Progress Ops', self.show_progress_ops, "#F57C00"),
            ('ℹ️ About', self.show_about, "#616161"),
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

        # Exit button
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

        # Model info display (will be updated after initialization)
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
        """Darken a hex color for hover effect."""
        # Simple darkening - remove # and darken each component
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        # Convert to RGB and darken by 20%
        r = max(0, int(hex_color[0:2], 16) - 30)
        g = max(0, int(hex_color[2:4], 16) - 30)
        b = max(0, int(hex_color[4:6], 16) - 30)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _initialize_in_background(self):
        """Initialize heavy components in background thread."""
        def init_components():
            try:
                # Initialize content manager
                self.after(0, lambda: self._update_status("Loading content..."))
                self.content_manager = ContentManager()
                
                # Initialize model
                self.after(0, lambda: self._update_status("Loading AI model..."))
                self.model_path = str(resolve_model_dir("satya_data/models/phi_1_5"))
                if not os.path.exists(self.model_path):
                    self.after(0, lambda: self._show_model_error(f"Model directory not found: {self.model_path}"))
                    return
                
                self.model_handler = ModelHandler(self.model_path)
                
                # Update model info
                self.after(0, self._update_model_info)
                self.after(0, lambda: self._update_status("Ready!"))
                
                self._initialization_done = True
            except Exception as e:
                self.after(0, lambda: self._show_model_error(f"Initialization error: {e}"))
        
        threading.Thread(target=init_components, daemon=True).start()
    
    def _update_status(self, message):
        """Update status message."""
        if hasattr(self, 'model_info_label'):
            self.model_info_label.configure(text=message)
    
    def _update_model_info(self):
        """Update model info display."""
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
        """Show model error without blocking."""
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
            if hasattr(self.model_handler, 'phi15_handler'):
                self.model_handler.phi15_handler.cleanup()
        except Exception:
            pass

    def _lazy_init_rag(self):
        """Initialize RAG system only when needed"""
        if not self._rag_initialized:
            try:
                chroma_db_path = str(resolve_chroma_db_dir("satya_data/chroma_db"))
                self.rag_engine = RAGRetrievalEngine(chroma_db_path=chroma_db_path)
                self._rag_initialized = True
            except Exception as e:
                self.rag_engine = None
                self._rag_initialized = True

    def _debounced_update(self, func, delay=50):
        """Prevent excessive UI updates"""
        if self._update_timer:
            self.after_cancel(self._update_timer)
        self._update_timer = self.after(delay, func)

    def _safe_destroy_widgets(self):
        """Safely destroy widgets without blocking"""
        try:
            for widget in self.main_frame.winfo_children():
                widget.destroy()
        except Exception:
            pass

    def on_login(self, username):
        """Handle user login and transition to main interface."""
        self.username = username
        self.welcome_view.pack_forget()
        self.sidebar.grid()
        self.sidebar_shown = True
        self.show_main_menu()

    def show_main_menu(self):
        """Show the main menu dashboard with welcome message."""
        if self._loading:
            return
        
        self._safe_destroy_widgets()
        
        # Create a modern dashboard layout
        dashboard_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        dashboard_frame.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Welcome header
        welcome_header = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        welcome_header.pack(fill='x', pady=(0, 30))
        
        welcome_title = ctk.CTkLabel(
            welcome_header,
            text=f"Welcome back, {self.username}! 👋",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#2E7D32"
        )
        welcome_title.pack(anchor='w')
        
        welcome_subtitle = ctk.CTkLabel(
            welcome_header,
            text="Your personal learning dashboard",
            font=ctk.CTkFont(size=18),
            text_color="#666666"
        )
        welcome_subtitle.pack(anchor='w', pady=(5, 0))
        
        # Feature cards
        features_frame = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        features_frame.pack(fill='both', expand=True)
        
        features = [
            ("📚", "Browse Subjects", "Explore a wide range of subjects and topics", self.show_browse, "#2E7D32"),
            ("❓", "Ask Questions", "Get instant answers from our AI assistant", self.show_ask, "#1976D2"),
            ("📊", "Track Progress", "See how you're doing and where to improve", self.show_progress, "#7B1FA2"),
        ]
        
        for icon, title, desc, command, color in features:
            card = ctk.CTkFrame(
                features_frame,
                corner_radius=15,
                fg_color="#FFFFFF",
                border_width=1,
                border_color="#E0E0E0"
            )
            card.pack(side='left', fill='both', expand=True, padx=10, pady=10)
            
            # Card content
            icon_label = ctk.CTkLabel(
                card,
                text=icon,
                font=ctk.CTkFont(size=48)
            )
            icon_label.pack(pady=(20, 10))
            
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=color
            )
            title_label.pack(pady=(0, 10))
            
            desc_label = ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=14),
                text_color="#666666",
                wraplength=200,
                justify='center'
            )
            desc_label.pack(pady=(0, 20), padx=20)
            
            action_btn = ctk.CTkButton(
                card,
                text="Get Started",
                command=command,
                fg_color=color,
                hover_color=self._darken_color(color),
                width=150,
                height=35
            )
            action_btn.pack(pady=(0, 20))

    def show_browse(self):
        """Show browse subjects view with non-blocking loading."""
        if self._loading:
            return
        
        # Wait for initialization if needed
        if not self.content_manager:
            self._show_loading_message("Initializing... Please wait.")
            self.after(100, self.show_browse)  # Retry after a short delay
            return
        
        self._loading = True
        self._safe_destroy_widgets()
        
        # Show loading with modern design
        loading_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        loading_frame.pack(fill='both', expand=True)
        
        loading_icon = ctk.CTkLabel(
            loading_frame,
            text="⏳",
            font=ctk.CTkFont(size=48)
        )
        loading_icon.pack(pady=40)
        
        loading_label = ctk.CTkLabel(
            loading_frame,
            text="Loading subjects...",
            font=ctk.CTkFont(size=18),
            text_color="#666666"
        )
        loading_label.pack(pady=10)
        
        self.update()
        
        def load_subjects():
            try:
                subjects = self.content_manager.get_all_subjects()
                
                def show_subjects():
                    self._safe_destroy_widgets()
                    view = SubjectView(self.main_frame, subjects, self.on_subject_selected, self.show_main_menu)
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
        """Show a loading message in the main frame."""
        self._safe_destroy_widgets()
        loading_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        loading_frame.pack(fill='both', expand=True)
        
        ctk.CTkLabel(
            loading_frame,
            text=message,
            font=ctk.CTkFont(size=16),
            text_color="#666666"
        ).pack(pady=40)

    def on_subject_selected(self, subject):
        if self._loading:
            return
        self._loading = True
        
        self.selected_subject = subject
        self._safe_destroy_widgets()
        
        # Show loading immediately
        loading = ctk.CTkLabel(self.main_frame, text="Loading topics...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        
        def load_topics():
            try:
                # Build flattened browseable topics (topic + nested subtopic paths with content)
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
        if self._loading:
            return
        self._loading = True
        
        # Topic entry can be a flattened dict from list_browseable_topics or a simple string
        if isinstance(topic, dict) and "topic" in topic:
            self.selected_topic = topic["topic"]
            self.selected_subtopic_path = topic.get("subtopic_path", [])
            display_label = topic.get("label", self.selected_topic)
        else:
            self.selected_topic = topic.get("name") if isinstance(topic, dict) else topic
            self.selected_subtopic_path = []
            display_label = self.selected_topic
        self._safe_destroy_widgets()
        
        # Show loading immediately
        loading = ctk.CTkLabel(self.main_frame, text=f"Loading concepts for {display_label}...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        
        def load_concepts():
            try:
                # Fetch concepts at specific nested path if provided
                concepts = self.content_manager.get_concepts_at_path(
                    self.selected_subject,
                    self.selected_topic,
                    self.selected_subtopic_path,
                )
                
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
        if self._loading:
            return
        self._loading = True
        
        self.selected_concept = concept_name
        self._safe_destroy_widgets()
        
        # Show loading immediately
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
        if self._loading:
            return
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
        if self._loading:
            return
        self._loading = True

        # Advanced correctness check using rubric-based scoring
        import re
        from difflib import SequenceMatcher

        STOPWORDS = set([
            "the","is","are","a","an","to","of","and","or","for","in","on","at","by","that",
            "this","it","as","be","with","from","into","their","its","they","them","can","will",
            "about","how","what","why","which","who","whose","when","where","than","then","also"
        ])

        def _stem(token: str) -> str:
            for suf in ("ing", "ed", "es", "s"):
                if token.endswith(suf) and len(token) - len(suf) >= 3:
                    return token[:-len(suf)]
            return token

        def tokenize(text: str):
            tokens = re.findall(r"[a-zA-Z]+", text.lower())
            return [_stem(t) for t in tokens if len(t) >= 3 and t not in STOPWORDS]

        def build_rubric(ref_texts):
            freq = {}
            for rt in ref_texts:
                for t in set(tokenize(rt)):
                    freq[t] = freq.get(t, 0) + 1
            common = [t for t, c in freq.items() if c >= max(1, len(ref_texts)//2)]
            if not common:
                common = [t for t, _ in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:8]]
            return set(common)

        explicit_rubric = set(question.get('rubric_keywords', []))
        acc = [a for a in question.get('acceptable_answers', []) if isinstance(a, str)]
        rubric = explicit_rubric if explicit_rubric else build_rubric(acc) if acc else set()
        user_tokens = set(tokenize(answer))

        keyword_overlap = len(user_tokens & rubric) / max(1, len(rubric)) if rubric else 0.0
        fuzzy_max = max((SequenceMatcher(None, answer.lower(), rt.lower()).ratio() for rt in acc), default=0.0)
        
        score = 0.8 * keyword_overlap + 0.2 * fuzzy_max
        
        threshold = float(question.get('rubric_threshold', 0.45))
        min_coverage = float(question.get('rubric_min_coverage', 0.50))
        correct = (score >= threshold) and (keyword_overlap >= min_coverage)

        # Update progress in background
        def update_progress():
            try:
                progress_manager.update_progress(
                    self.username, self.selected_subject, self.selected_topic, self.selected_concept, question['question'], correct
                )
            except Exception:
                pass
        
        threading.Thread(target=update_progress, daemon=True).start()
        
        # Show feedback immediately
        self._safe_destroy_widgets()
        
        if correct:
            msg = "✓ Correct!"
            color = "#43a047"
        else:
            msg = "✗ Not quite right."
            color = "#e53935"
        
        label = ctk.CTkLabel(self.main_frame, text=msg, font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
        label.pack(pady=(40, 10))
        
        # Hints
        if not correct and question.get('hints'):
            ctk.CTkLabel(self.main_frame, text="Hints:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
            for hint in question['hints']:
                ctk.CTkLabel(self.main_frame, text=f"• {hint}", font=ctk.CTkFont(size=15)).pack(anchor='w', padx=40)
        
        # Explanation
        if question.get('explanation'):
            ctk.CTkLabel(self.main_frame, text="Explanation:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
            ctk.CTkLabel(self.main_frame, text=question['explanation'], font=ctk.CTkFont(size=15), wraplength=500, justify='left').pack(pady=(0, 10))
        
        # Next button
        ctk.CTkButton(self.main_frame, text="Next Question", command=self.next_question).pack(pady=30)
        self._loading = False

    def next_question(self):
        if self._loading:
            return
        self.question_index += 1
        self.show_question()

    def show_concept_complete(self):
        if self._loading:
            return
        self._loading = True
        
        self._safe_destroy_widgets()
        ctk.CTkLabel(self.main_frame, text="You've completed all questions for this concept!", font=ctk.CTkFont(size=18)).pack(pady=60)
        ctk.CTkButton(self.main_frame, text="Back to Concepts", command=lambda: self.on_topic_selected(self.selected_topic)).pack(pady=20)
        self._loading = False

    def show_ask(self):
        if self._loading:
            return
        self._loading = True
        
        self._safe_destroy_widgets()
        self.ask_view = AskQuestionView(self.main_frame, self.on_ask_submit, self.show_main_menu, self.on_ask_openai)
        self.ask_view.pack(fill='both', expand=True)
        self._loading = False

    def on_ask_openai(self, question):
        if self._loading:
            return
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

    def on_ask_submit(self, question, answer_length="medium"):
        if self._loading:
            return
        self._loading = True
        
        self.ask_view.set_loading(True)
        
        def worker():
            try:
                # Lazy initialize RAG if needed
                if not self._rag_initialized:
                    self._lazy_init_rag()
                
                normalized_question = question.strip().capitalize()
                
                # Use optimized non-blocking RAG helper (fast, with timeout)
                from system.rag.rag_helper import get_context_non_blocking
                
                rag_context, source_info = get_context_non_blocking(
                    self.rag_engine,
                    question,
                    content_manager=self.content_manager,
                    timeout_seconds=0.5  # 0.5 second timeout - fast fallback to structured content
                )
                
                # Get related content for display (non-blocking, quick)
                related = []
                if source_info == "Structured content":
                    try:
                        relevant = self.content_manager.search_content(question)
                        if relevant and len(relevant) > 1:
                            related = [f"{item['subject']} > {item['topic']} > {item['concept']}" for item in relevant[1:3]]
                    except Exception:
                        pass

                # Stream answer from local model for real-time display
                accumulated_answer = ""
                
                def update_answer(token):
                    """Update the answer display with new token."""
                    nonlocal accumulated_answer
                    accumulated_answer += token
                    self.after(0, lambda t=token: self.ask_view.append_answer_token(t))
                
                # Start streaming
                try:
                    for token in self.model_handler.get_answer_stream(
                        normalized_question,
                        rag_context,
                        answer_length,
                    ):
                        update_answer(token)
                    
                    # Calculate confidence after streaming completes
                    if accumulated_answer and len(accumulated_answer.strip()) >= 10:
                        # Quick confidence calculation - focuses on answer quality
                        answer_lower = accumulated_answer.lower()
                        has_rag_context = rag_context and len(rag_context.strip()) > 50
                        word_count = len(accumulated_answer.split())
                        
                        if word_count < 5:
                            confidence = 0.3
                        else:
                            has_structure = accumulated_answer.count(".") >= 2
                            has_definition = any(phrase in answer_lower for phrase in ["is a", "is an", "are", "means", "refers to"])
                            has_examples = any(word in answer_lower for word in ["example", "like", "such as"])
                            is_complete = word_count >= 15 and has_structure
                            
                            # Base confidence - high for complete, quality answers
                            if is_complete:
                                base_score = 0.85
                            elif has_structure:
                                base_score = 0.75
                            else:
                                base_score = 0.65
                            
                            # Quality boosts
                            if has_definition:
                                base_score += 0.05
                            if has_examples:
                                base_score += 0.05
                            if has_structure and word_count >= 20:
                                base_score += 0.05
                            
                            # Knowledge source boost
                            if has_rag_context:
                                base_score += 0.10  # RAG = study materials
                            else:
                                base_score += 0.05  # Own knowledge is also reliable
                            
                        confidence = min(1.0, base_score)
                    else:
                        confidence = 0.1
                    
                    hints = []
                    if confidence < 0.7:
                        try:
                            hints = self.model_handler.get_hints(normalized_question, rag_context)
                        except Exception:
                            pass
                    
                    def show_result():
                        if not accumulated_answer or len(accumulated_answer.strip()) < 5 or confidence < 0.1:
                            fallback_msg = "I'm not sure about that. Here's some related information:"
                            self.ask_view.set_result(fallback_msg + "\n\n" + (rag_context or ""), 0.0, hints, related, source_info)
                        else:
                            # Pass question for diagram generation
                            self.ask_view.finalize_answer(confidence, hints, related, source_info, question=normalized_question)
                        self._loading = False
                    
                    self.after(0, show_result)
                    
                except Exception as stream_error:
                    # Fallback to non-streaming if streaming fails
                    def fallback():
                        try:
                            answer, confidence = self.model_handler.get_answer(
                                normalized_question,
                                rag_context,
                                answer_length,
                            )
                            
                            hints = []
                            if confidence < 0.7:
                                try:
                                    hints = self.model_handler.get_hints(normalized_question, rag_context)
                                except Exception:
                                    pass
                            
                            def show_result():
                                if not answer or len(answer.strip()) < 5 or confidence < 0.1:
                                    fallback_msg = "I'm not sure about that. Here's some related information:"
                                    self.ask_view.set_result(fallback_msg + "\n\n" + (rag_context or ""), 0.0, hints, related, source_info)
                                else:
                                    self.ask_view.set_result(answer, confidence, hints, related, source_info)
                                self._loading = False
                            
                            self.after(0, show_result)
                        except Exception as e:
                            def show_error():
                                mb.showerror("Ask Question", f"Failed to answer: {e}")
                                self.ask_view.set_result("An error occurred. Please try again.", 0.0, None, None, "Error")
                                self._loading = False
                            self.after(0, show_error)
                    
                    fallback()
                
            except Exception as e:
                def show_error():
                    mb.showerror("Ask Question", f"Failed to answer: {e}")
                    self.ask_view.set_result("An error occurred. Please try again.", 0.0, None, None, "Error")
                    self._loading = False
                
                self.after(0, show_error)
        
        threading.Thread(target=worker, daemon=True).start()

    def show_progress(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Show loading with spinner
        loading_frame = ctk.CTkFrame(self.main_frame)
        loading_frame.pack(expand=True, fill='both', pady=100)
        
        loading_label = ctk.CTkLabel(loading_frame, text="Loading your progress...", font=ctk.CTkFont(size=18))
        loading_label.pack(pady=20)
        
        spinner_label = ctk.CTkLabel(loading_frame, text="⏳", font=ctk.CTkFont(size=24))
        spinner_label.pack(pady=10)
        
        self.main_frame.update()
        
        # Load progress in background thread
        def load_progress_worker():
            try:
                progress = progress_manager.load_progress(self.username)
                total_questions = 0
                total_correct = 0
                mastered = []
                weak = []
                subject_stats = {}
                
                # Process progress data
                for subject, topics in progress.items():
                    subject_stats[subject] = {'total': 0, 'correct': 0}
                    for topic, concepts in topics.items():
                        for concept, data in concepts.items():
                            for q in data.get('questions', []):
                                total_questions += q['attempts']
                                total_correct += q['correct']
                                subject_stats[subject]['total'] += q['attempts']
                                subject_stats[subject]['correct'] += q['correct']
                                if q['correct'] >= 3:
                                    mastered.append(f"{subject} > {topic} > {concept}")
                                elif q['attempts'] >= 2 and q['correct'] == 0:
                                    weak.append(f"{subject} > {topic} > {concept} > {q['question']}")
                
                # Add subjects with no progress
                for subject in self.content_manager.get_all_subjects():
                    if subject not in subject_stats:
                        subject_stats[subject] = {'total': 0, 'correct': 0}
                
                # Calculate percentages
                for subject, stats in subject_stats.items():
                    if stats['total'] > 0:
                        stats['pct'] = stats['correct'] / stats['total'] * 100
                    else:
                        stats['pct'] = 0.0
                
                score = (total_correct / total_questions * 100) if total_questions else 0
                stats_dict = {'total': total_questions, 'correct': total_correct, 'score': score}
                
                # Get next concept suggestion
                next_concept = self.content_manager.suggest_next_concept(self.username)
                if next_concept:
                    next_concept_str = f"Try learning about: {next_concept['concept']['name']} in {next_concept['topic']} ({next_concept['subject']})"
                else:
                    next_concept_str = None
                
                # Show progress view in main thread
                def show_progress_view():
                    for widget in self.main_frame.winfo_children():
                        widget.destroy()
                    view = ProgressView(self.main_frame, stats_dict, mastered, weak, subject_stats, next_concept_str, self.show_main_menu)
                    view.pack(fill='both', expand=True)
                
                self.after(0, show_progress_view)
                
            except Exception as e:
                def show_error():
                    for widget in self.main_frame.winfo_children():
                        widget.destroy()
                    mb.showerror("Error", f"Failed to load progress: {e}")
                    self.show_main_menu()
                
                self.after(0, show_error)
        
        threading.Thread(target=load_progress_worker, daemon=True).start()

    def show_progress_ops(self):
        if self._loading:
            return
        self._loading = True
        
        self._safe_destroy_widgets()
        view = ProgressOpsView(self.main_frame, self.export_progress, self.import_progress, self.reset_progress, self.show_main_menu)
        view.pack(fill='both', expand=True)
        self._loading = False

    def show_about(self):
        if self._loading:
            return
        self._loading = True
        
        self._safe_destroy_widgets()
        view = AboutView(self.main_frame, self.show_main_menu)
        view.pack(fill='both', expand=True)
        self._loading = False

    def export_progress(self):
        try:
            progress = progress_manager.load_progress(self.username)
            if not progress:
                mb.showinfo("Export Progress", "No progress to export.")
                return
            file = fd.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], title="Export Progress")
            if file:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(progress, f, indent=2, ensure_ascii=False)
                mb.showinfo("Export Progress", f"Progress exported to {os.path.basename(file)}.")
        except Exception as e:
            mb.showerror("Export Progress", f"Failed to export: {e}")

    def import_progress(self):
        try:
            file = fd.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Import Progress")
            if file:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                progress_manager.save_progress(self.username, data)
                mb.showinfo("Import Progress", "Progress imported successfully.")
        except Exception as e:
            mb.showerror("Import Progress", f"Failed to import: {e}")

    def reset_progress(self):
        try:
            if mb.askyesno("Reset Progress", "Are you sure you want to reset all your progress? This cannot be undone."):
                progress_manager.save_progress(self.username, {})
                mb.showinfo("Reset Progress", "Progress has been reset.")
                self.show_main_menu()
        except Exception as e:
            mb.showerror("Reset Progress", f"Failed to reset: {e}")

if __name__ == '__main__':
    app = NEBeduApp()
    app.mainloop()