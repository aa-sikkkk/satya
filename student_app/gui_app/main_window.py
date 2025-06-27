import customtkinter as ctk
from student_app.gui_app.views import WelcomeView, SubjectView, TopicView, ConceptView, ConceptDetailView, QuestionView, ProgressView, AskQuestionView, ProgressOpsView
from system.data_manager.content_manager import ContentManager
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

class NEBeduApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('NEBedu Learning Companion')
        self.geometry('900x600')
        ctk.set_appearance_mode('light')
        ctk.set_default_color_theme('green')
        self.username = None
        self.content_manager = ContentManager()
        # Model path logic (same as CLI)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(base_dir, "ai_model", "exported_model")
        if not os.path.exists(model_path):
            mb.showerror("Model Error", f"Model directory not found: {model_path}")
            raise FileNotFoundError(f"Model directory not found: {model_path}")
        try:
            self.model_handler = ModelHandler(model_path)
            self.model_handler.phi2_handler.load_model()
            # Reduce max_tokens for faster answers
            self.model_handler.phi2_handler.config['max_tokens'] = 60
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
            self.model_handler.phi2_handler.cleanup()
        except Exception:
            pass

    def on_login(self, username):
        self.username = username
        self.welcome_view.pack_forget()
        self.sidebar.grid()
        self.show_main_menu()

    def show_main_menu(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        label = ctk.CTkLabel(
            self.main_frame,
            text=f"Welcome, {self.username}!\n\n- Browse subjects and study organized content\n- Ask questions and get AI-powered answers\n- Track your learning progress\n\nLet\'s start your learning journey! 🚀",
            font=ctk.CTkFont(size=18),
            justify='left',
        )
        label.pack(pady=60, padx=40)

    def show_browse(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        loading = ctk.CTkLabel(self.main_frame, text="Loading subjects...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        try:
            subjects = self.content_manager.get_all_subjects()
            loading.destroy()
            view = SubjectView(self.main_frame, subjects, self.on_subject_selected, self.show_main_menu)
            view.pack(fill='both', expand=True)
        except Exception as e:
            loading.destroy()
            mb.showerror("Error", f"Failed to load subjects: {e}")

    def on_subject_selected(self, subject):
        self.selected_subject = subject
        topics = self.content_manager.get_all_topics(subject)
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        view = TopicView(self.main_frame, topics, self.on_topic_selected, self.show_browse)
        view.pack(fill='both', expand=True)

    def on_topic_selected(self, topic):
        self.selected_topic = topic
        concepts = self.content_manager.get_all_concepts(self.selected_subject, topic)
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        view = ConceptView(self.main_frame, concepts, self.on_concept_selected, lambda: self.on_subject_selected(self.selected_subject))
        view.pack(fill='both', expand=True)

    def on_concept_selected(self, concept_name):
        self.selected_concept = concept_name
        concept = self.content_manager.get_concept(self.selected_subject, self.selected_topic, concept_name)
        self.selected_concept_data = concept
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        view = ConceptDetailView(self.main_frame, concept, self.start_questions, lambda: self.on_topic_selected(self.selected_topic))
        view.pack(fill='both', expand=True)

    def start_questions(self):
        self.question_index = 0
        self.show_question()

    def show_question(self):
        concept = self.selected_concept_data
        questions = concept.get('questions', [])
        if self.question_index >= len(questions):
            self.show_concept_complete()
            return
        q = questions[self.question_index]
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        view = QuestionView(self.main_frame, q['question'], lambda ans: self.on_answer_submitted(ans, q), lambda: self.on_concept_selected(self.selected_concept))
        view.pack(fill='both', expand=True)

    def on_answer_submitted(self, answer, question):
        # Check correctness (simple substring match for now)
        correct = any(ans.lower() in answer.lower() for ans in question.get('acceptable_answers', []))
        progress_manager.update_progress(
            self.username, self.selected_subject, self.selected_topic, self.selected_concept, question['question'], correct
        )
        # Show feedback, hints, and explanation
        for widget in self.main_frame.winfo_children():
            widget.destroy()
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

    def next_question(self):
        self.question_index += 1
        self.show_question()

    def show_concept_complete(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.main_frame, text="You've completed all questions for this concept!", font=ctk.CTkFont(size=18)).pack(pady=60)
        ctk.CTkButton(self.main_frame, text="Back to Concepts", command=lambda: self.on_topic_selected(self.selected_topic)).pack(pady=20)

    def show_ask(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.ask_view = AskQuestionView(self.main_frame, self.on_ask_submit, self.show_main_menu)
        self.ask_view.pack(fill='both', expand=True)

    def on_ask_submit(self, question):
        self.ask_view.set_loading(True)
        def worker():
            try:
                relevant = self.content_manager.search_content(question)
                if relevant:
                    subject = relevant[0]['subject']
                    topic = relevant[0]['topic']
                    concept = relevant[0]['concept']
                    concept_data = self.content_manager.get_concept(subject, topic, concept)
                    answer = None
                    confidence = 0.0
                    hints = []
                    explanation = None
                    if concept_data and 'questions' in concept_data:
                        for q in concept_data['questions']:
                            if isinstance(q, dict) and 'question' in q:
                                ratio = difflib.SequenceMatcher(None, q['question'].lower(), question.lower()).ratio()
                                if ratio > 0.6:
                                    if 'acceptable_answers' in q and q['acceptable_answers']:
                                        answer = q['acceptable_answers'][0]
                                        confidence = 0.9
                                        hints = q.get('hints', [])
                                        explanation = q.get('explanation', None)
                                        break
                    if not answer:
                        context = relevant[0]['summary']
                        answer, confidence = self.model_handler.get_answer(question, context)
                        try:
                            hints = self.model_handler.get_hints(question, context)
                        except Exception:
                            hints = []
                    related = [f"{item['subject']} > {item['topic']} > {item['concept']}" for item in relevant[1:3]]
                    self.after(0, lambda: self.ask_view.set_result(answer, confidence, hints, related))
                else:
                    context = self.content_manager.get_default_context()
                    answer, confidence = self.model_handler.get_answer(question, context)
                    try:
                        hints = self.model_handler.get_hints(question, context)
                    except Exception:
                        hints = []
                    self.after(0, lambda: self.ask_view.set_result(answer, confidence, hints, None))
            except Exception as e:
                self.after(0, lambda: (
                    mb.showerror("Ask Question", f"Failed to answer: {e}"),
                    self.ask_view.set_result("An error occurred. Please try again.", 0.0, None, None)
                ))
        threading.Thread(target=worker, daemon=True).start()

    def show_progress(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        loading = ctk.CTkLabel(self.main_frame, text="Loading progress...", font=ctk.CTkFont(size=16))
        loading.pack(pady=40)
        self.main_frame.update()
        try:
            progress = progress_manager.load_progress(self.username)
            total_questions = 0
            total_correct = 0
            mastered = []
            weak = []
            subject_stats = {}
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
            for subject in self.content_manager.get_all_subjects():
                if subject not in subject_stats:
                    subject_stats[subject] = {'total': 0, 'correct': 0}
            for subject, stats in subject_stats.items():
                if stats['total'] > 0:
                    stats['pct'] = stats['correct'] / stats['total'] * 100
                else:
                    stats['pct'] = 0.0
            score = (total_correct / total_questions * 100) if total_questions else 0
            stats_dict = {'total': total_questions, 'correct': total_correct, 'score': score}
            next_concept = self.content_manager.suggest_next_concept(self.username)
            if next_concept:
                next_concept_str = f"Try learning about: {next_concept['concept']['name']} in {next_concept['topic']} ({next_concept['subject']})"
            else:
                next_concept_str = None
            loading.destroy()
            view = ProgressView(self.main_frame, stats_dict, mastered, weak, subject_stats, next_concept_str, self.show_main_menu)
            view.pack(fill='both', expand=True)
        except Exception as e:
            loading.destroy()
            mb.showerror("Error", f"Failed to load progress: {e}")

    def show_progress_ops(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        view = ProgressOpsView(self.main_frame, self.export_progress, self.import_progress, self.reset_progress, self.show_main_menu)
        view.pack(fill='both', expand=True)

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