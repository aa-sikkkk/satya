import customtkinter as ctk
from student_app.gui_app.views import WelcomeView, SubjectView, TopicView, ConceptView, ConceptDetailView, QuestionView, ProgressView, AskQuestionView, ProgressOpsView
from system.data_manager.content_manager import ContentManager
from system.rag.rag_retrieval_engine import RAGRetrievalEngine
from student_app.progress import progress_manager
from ai_model.model_utils.model_handler import ModelHandler
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
    def __init__(self):
        super().__init__()
        self.title('Satya: Learning Companion')
        self.geometry('900x600')
        ctk.set_appearance_mode('light')
        ctk.set_default_color_theme('green')
        
        # Performance optimizations
        self._cache = {}  # Widget and data caching
        self._loading = False  # Prevent multiple simultaneous operations
        self._update_timer = None  # Debounced updates
        
        self.username = None
        self.content_manager = ContentManager()
        
        # Initialize RAG system (lazy)
        self.rag_engine = None
        self._rag_initialized = False
        
        # Model path logic (updated for new architecture)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(base_dir, "satya_data", "models", "phi_1_5")
        if not os.path.exists(model_path):
            mb.showerror("Model Error", f"Model directory not found: {model_path}")
            raise FileNotFoundError(f"Model directory not found: {model_path}")
        
        try:
            self.model_handler = ModelHandler(model_path)
        except Exception as e:
            mb.showerror("Model Error", f"Could not initialize the AI model: {e}")
            raise
        
        atexit.register(self.cleanup_model)
        self.selected_subject = None
        self.selected_topic = None
        self.selected_concept = None
        self.selected_concept_data = None
        self.question_index = 0

        # Main container
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill='both', expand=True)

        # Sidebar (hidden until login)
        self.sidebar = ctk.CTkFrame(self.container, width=180, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky='ns')
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_remove()

        # Logo image at the top of the sidebar
        logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
        logo_img = ctk.CTkImage(light_image=Image.open(logo_path), size=(120, 120))
        self.logo_image_label = ctk.CTkLabel(self.sidebar, image=logo_img, text="")
        self.logo_image_label.pack(pady=(20, 10))

        self.btn_browse = ctk.CTkButton(self.sidebar, text='Browse Subjects', command=self.show_browse)
        self.btn_browse.pack(pady=10, fill='x', padx=20)
        self.btn_ask = ctk.CTkButton(self.sidebar, text='Ask Question', command=self.show_ask)
        self.btn_ask.pack(pady=10, fill='x', padx=20)
        self.btn_progress = ctk.CTkButton(self.sidebar, text='Progress', command=self.show_progress)
        self.btn_progress.pack(pady=10, fill='x', padx=20)
        self.btn_ops = ctk.CTkButton(self.sidebar, text='Progress Ops', command=self.show_progress_ops)
        self.btn_ops.pack(pady=10, fill='x', padx=20)
        self.btn_exit = ctk.CTkButton(self.sidebar, text='Exit', fg_color='#e57373', hover_color='#ef5350', command=self.quit)
        self.btn_exit.pack(pady=(40,0), fill='x', padx=20)

        # Main content area
        self.main_frame = ctk.CTkFrame(self.container, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky='nsew', padx=30, pady=30)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)

        # Start with WelcomeView
        self.welcome_view = WelcomeView(self.main_frame, self.on_login)
        self.welcome_view.pack(fill='both', expand=True)

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
                self.rag_engine = RAGRetrievalEngine()
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
        self.username = username
        self.welcome_view.pack_forget()
        self.sidebar.grid()
        self.show_main_menu()

    def show_main_menu(self):
        self._safe_destroy_widgets()
        label = ctk.CTkLabel(
            self.main_frame,
            text=f"Welcome, {self.username}!\n\n- Browse subjects and study organized content\n- Ask questions with RAG-powered intelligent answers\n- Choose answer length (very short to very long)\n- Track your learning progress\n\nLet\'s start your learning journey! 🚀",
            font=ctk.CTkFont(size=18),
            justify='left',
        )
        label.pack(pady=60, padx=40)

    def show_browse(self):
        if self._loading:
            return
        self._loading = True
        
        self._safe_destroy_widgets()
        
        # Show loading immediately
        loading = ctk.CTkLabel(self.main_frame, text="Loading subjects...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        
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
        
        # Check correctness (simple substring match for now)
        correct = any(ans.lower() in answer.lower() for ans in question.get('acceptable_answers', []))
        
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
        self.ask_view = AskQuestionView(self.main_frame, self.on_ask_submit, self.show_main_menu)
        self.ask_view.pack(fill='both', expand=True)
        self._loading = False

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
                
                # Text normalization for better model understanding
                normalized_question = question
                if question.isupper():
                    normalized_question = question.capitalize()
                elif question.islower():
                    normalized_question = question.capitalize()
                
                # Step 1: Try RAG retrieval first (non-blocking)
                rag_context = None
                source_info = "RAG-powered content discovery"
                related = []  # Initialize related variable
                
                if self.rag_engine:
                    try:
                        rag_results = self.rag_engine.retrieve_relevant_content(question, max_results=3)
                        if rag_results and rag_results.get('chunks'):
                            # Apply lightweight distance filtering if available
                            chunks = rag_results['chunks']
                            safe_chunks = []
                            for ch in chunks:
                                dist = ch.get('distance', 0.0)
                                if dist is None or dist <= 0.35:
                                    safe_chunks.append(ch)
                            if safe_chunks:
                                rag_context = "\n\n".join([ch['content'] for ch in safe_chunks])
                                source_info = f"RAG found {len(safe_chunks)} relevant content chunks"
                    except Exception:
                        # RAG failed, continue with fallback
                        pass
                
                # Step 2: Fallback to structured content search
                if not rag_context:
                    relevant = self.content_manager.search_content(question)
                    if relevant:
                        subject = relevant[0]['subject']
                        topic = relevant[0]['topic']
                        concept = relevant[0]['concept']
                        concept_data = self.content_manager.get_concept(subject, topic, concept)
                        if concept_data and 'questions' in concept_data:
                            for q in concept_data['questions']:
                                if isinstance(q, dict) and 'question' in q:
                                    ratio = difflib.SequenceMatcher(None, q['question'].lower(), question.lower()).ratio()
                                    if ratio > 0.7:
                                        if 'acceptable_answers' in q and q['acceptable_answers']:
                                            answer = q['acceptable_answers'][0]
                                            confidence = 0.9
                                            hints = q.get('hints', [])
                                            related = [f"{item['subject']} > {item['topic']} > {item['concept']}" for item in relevant[1:3]]
                                            
                                            def show_structured_result():
                                                self.ask_view.set_result(answer, confidence, hints, related, source_info="Structured content match")
                                                self._loading = False
                                            self.after(0, show_structured_result)
                                            return
                        rag_context = relevant[0]['summary']
                        source_info = "Structured content search"
                        related = [f"{item['subject']} > {item['topic']} > {item['concept']}" for item in relevant[1:3]]
                
                # Step 3: Use Phi 1.5 with context
                if not rag_context:
                    rag_context = "General knowledge about computer science and English for Grade 10 students."
                    source_info = "General knowledge (no specific content found)"
                
                # Get answer from Phi 1.5
                answer, confidence = self.model_handler.get_answer(normalized_question, rag_context, answer_length)
                
                # Get hints if confidence is low
                hints = []
                if confidence < 0.7:
                    try:
                        hints = self.model_handler.get_hints(normalized_question, rag_context)
                    except Exception:
                        pass
                
                # Show result
                def show_result():
                    if not answer or (isinstance(answer, str) and len(answer.strip()) < 5) or confidence < 0.1:
                        # Very low confidence - show context and fallback
                        fallback_msg = "I'm not sure about that. Let me help you find the right information:"
                        self.ask_view.set_result(fallback_msg + "\n\n" + rag_context, 0.0, hints, related, source_info)
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