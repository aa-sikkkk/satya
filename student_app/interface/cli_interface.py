# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
CLI Interface Module

This module provides the command-line interface for students to interact with
the Satya learning system.
"""

import os
import sys
import logging
import difflib
from typing import Optional, List, Dict, Any, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from system.data_manager.content_manager import ContentManager, get_most_relevant_sentence
from ai_model.model_utils.model_handler import ModelHandler
from student_app.progress import progress_manager
from system.performance.performance_utils import timeit, log_resource_usage
from system.security.security_utils import validate_username, sanitize_filepath, log_security_event, validate_content_input
from student_app.learning.openai_proxy_client import OpenAIProxyClient
import re
from system.diagrams import generate_diagram_content
from system.rag.rag_retrieval_engine import RAGRetrievalEngine
from system.utils.resource_path import resolve_model_dir, resolve_content_dir, resolve_chroma_db_dir
from student_app.interface.cli_renderer import CLIRenderer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('satya.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

console = Console()

style = Style.from_dict({
    'prompt': 'ansicyan bold',
    'input': 'ansigreen',
})

bindings = KeyBindings()

from rich.prompt import Prompt as _Prompt

def patched_confirm_ask(prompt, default=False):
    yes_choices = {"y", "yes"}
    no_choices = {"n", "no"}
    prompt_str = f"{prompt} [y/n]"
    while True:
        answer = _Prompt.ask(prompt_str).strip().lower()
        if answer in yes_choices:
            return True
        if answer in no_choices:
            return False
        console.print("[red]Please enter 'y' or 'n'.[/red]")

Confirm.ask = staticmethod(patched_confirm_ask)

class CLIInterface:
    """
    Command-line interface for the Satya learning system.
    
    Attributes:
        content_manager (ContentManager): Manager for educational content
        model_handler (ModelHandler): Handler for AI model
        session (PromptSession): Interactive prompt session
        username (str): The entered username
        openai_client (OpenAIProxyClient): Client for OpenAI proxy
    """
    
    def __init__(self, content_dir: str, model_path: str):
        """
        Initialize the CLI interface.
        
        Args:
            content_dir (str): Path to content directory
            model_path (str): Path to model directory
        """
        console.print("[cyan]Initializing Satya CLI...[/cyan]")
        self.content_manager = ContentManager(content_dir)
        
        # Initialize Model Handler
        console.print("[dim]Loading AI Model...[/dim]")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")
            
        try:
            self.model_handler = ModelHandler(model_path)
        except Exception as e:
            logger.error(f"Failed to initialize Phi 1.5 model: {str(e)}")
            console.print(Panel(
                "[red]Error: Could not initialize the Phi 1.5 model. Please check the model files and try again.[/red]",
                title="Model Error",
                border_style="red"
            ))
            raise

        # Initialize RAG Engine
        console.print("[dim]Initializing Knowledge Engine...[/dim]")
        try:
            chroma_db_path = str(resolve_chroma_db_dir("satya_data/chroma_db"))
            
            self.rag_engine = RAGRetrievalEngine(
                chroma_db_path=chroma_db_path,
                llm_handler=self.model_handler
            )
            
            # Warm up RAG engine (loads embeddings)
            console.print("[dim]Warming up Knowledge Engine...[/dim]")
            self.rag_engine.warm_up()
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {str(e)}")
            console.print(Panel(
                "[yellow]Warning: RAG engine not available. Using basic content search.[/yellow]",
                title="RAG Warning",
                border_style="yellow"
            ))
            self.rag_engine = None
            
        self.session = PromptSession(key_bindings=bindings)
        self.username = self._prompt_username()
        # Sticky memory for the most recent QA context
        self._last_question_text: Optional[str] = None
        self._last_acceptable_answers: Optional[List[str]] = None
        self._last_concept_summary: Optional[str] = None
        self._show_welcome_message()
        self._show_model_info()
        # Configure OpenAI proxy client with environment variables or defaults
        proxy_url = os.getenv("OPENAI_PROXY_URL")
        proxy_api_key = os.getenv("OPENAI_PROXY_KEY")
        self.openai_client = OpenAIProxyClient(proxy_url=proxy_url, api_key=proxy_api_key)
        
        
        # Grade/subject state for diagram filtering
        self.selected_grade = None
        self.selected_subject = None
        
    def _show_welcome_message(self) -> None:
        """Display welcome message and quick start guide."""
        CLIRenderer.show_welcome_message()
        
    def _show_help(self, context: str = "main") -> None:
        """Display context-specific help."""
        CLIRenderer.show_help(context)
        
    def _show_model_info(self) -> None:
        """Display information about the current AI model."""
        try:
            model_info = self.model_handler.get_model_info()
            CLIRenderer.show_model_info(model_info)
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            CLIRenderer.show_model_info(None)
        
    def _prompt_username(self) -> str:
        """
        Prompt the user for a username at the start of the session.
        Returns:
            str: The entered username
        """
        console.print(Panel(
            "[bold cyan]Welcome to Satya![/bold cyan]\n"
            "Please enter your username to track your progress.",
            border_style="cyan"
        ))
        while True:
            username = Prompt.ask("Username", default="student")
            if validate_username(username):
                return username.strip()
            else:
                log_security_event(f"Invalid username attempt: {username}")
                console.print("[red]Invalid username. Use 3-32 alphanumeric characters or underscores.[/red]")
        
    def _create_menu(self, title: str, options: List[str]) -> str:
        """Create and display a menu."""
        CLIRenderer.render_menu(title, options)
        
        while True:
            try:
                # Use prompt_toolkit's session for input
                choice = self.session.prompt("Select an option (1-{}) ".format(len(options)))
                
                if choice.lower() in ['help', 'h']:
                    self._show_help()
                    continue
                    
                if choice.lower() in ['exit', 'q']:
                    if Confirm.ask("Are you sure you want to exit?"):
                        console.print("[bold green]Thank you for using Satya. Goodbye![/bold green]")
                        sys.exit(0)
                    continue
                
                # Check if input is a valid number
                if choice.isdigit() and 1 <= int(choice) <= len(options):
                    return options[int(choice) - 1]
                    
                console.print("[red]Please enter a number between 1 and {}[/red]".format(len(options)))
                
            except Exception as e:
                console.print("[red]Invalid choice. Please try again.[/red]")
    
    def _create_menu_with_index(self, title: str, options: List[str]) -> Any:
        """Create and display a menu and return both index (1-based) and label."""
        CLIRenderer.render_menu(title, options)
        while True:
            try:
                choice = self.session.prompt("Select an option (1-{}) ".format(len(options)))
                if choice.lower() in ['help', 'h']:
                    self._show_help()
                    continue
                if choice.lower() in ['exit', 'q']:
                    if Confirm.ask("Are you sure you want to exit?"):
                        console.print("[bold green]Thank you for using Satya. Goodbye![/bold green]")
                        sys.exit(0)
                    continue
                if choice.isdigit() and 1 <= int(choice) <= len(options):
                    idx = int(choice)
                    return idx, options[idx - 1]
                console.print("[red]Please enter a number between 1 and {}[/red]".format(len(options)))
            except Exception:
                console.print("[red]Invalid choice. Please try again.[/red]")
            
    def _display_concept(self, concept: Dict[str, Any]) -> None:
        """Display a concept and its content."""
        CLIRenderer.display_concept(concept)
                
    def _display_question(self, question: Dict[str, Any], subject=None, topic=None, concept=None, concept_summary=None) -> None:
        """
        Display a question and handle user interaction.
        
        Args:
            question (Dict[str, Any]): Question data
            subject (str): The selected subject
            topic (str): The selected topic
            concept (str): The selected concept
            concept_summary (str): The summary of the concept (for fallback explanation)
        """
        # Show question number if available
        question_num = question.get('number', '')
        question_title = f"Question {question_num}" if question_num else "Question"
        
        console.print(Panel(
            f"[bold yellow]{question['question']}[/bold yellow]",
            title=question_title,
            border_style="yellow"
        ))
        
        # Show question type if available
        if 'type' in question:
            console.print(f"[dim]Type: {question['type']}[/dim]")
            
        # Update sticky memory for this question
        try:
            self._last_question_text = question.get('question')
        except Exception:
            self._last_question_text = None
        try:
            self._last_concept_summary = concept_summary
        except Exception:
            self._last_concept_summary = None
        # Get user's answer (use prompt_toolkit session for consistent input handling)
        answer = self.session.prompt("Your answer: ")
        
        # Use internal grading logic matching GUI
        correct, explanation = self._grade_answer_with_ai(question['question'], answer, question.get('answer', ''))
        
        if correct:
            console.print(Panel(
                "[bold green]✓ Correct![/bold green]",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[bold red]✗ Not quite right.[/bold red]",
                border_style="red"
            ))
            
            # Offer hints with better formatting
            if Confirm.ask("Would you like a hint?"):
                for i, hint in enumerate(question.get('hints', []), 1):
                    console.print(Panel(
                        f"[yellow]Hint {i}:[/yellow] {hint}",
                        border_style="yellow"
                    ))
                    if not Confirm.ask("Would you like another hint?"):
                        break
                        
        # Offer a brief explanation; default off when correct, on when incorrect
        want_expl = Confirm.ask(
            "Would you like a brief explanation?",
            default=(not correct)
        )
        if want_expl and explanation:
            console.print(Panel(
                explanation,
                title="Explanation",
                border_style="blue"
            ))
            
            # Show related concepts if available
            if 'related_concepts' in question:
                console.print("\n[bold cyan]Related Concepts:[/bold cyan]")
                for concept in question['related_concepts']:
                    console.print(f"• {concept}")
            
        # Update progress after question attempt
        if subject and topic and concept:
            progress_manager.update_progress(
                self.username, subject, topic, concept, question['question'], correct
            )
            # Compute simple progress summary inline
            try:
                pdata = progress_manager.load_progress(self.username)
                qlist = (
                    pdata.get(subject, {})
                         .get(topic, {})
                         .get(concept, {})
                         .get('questions', [])
                )
                total = len(qlist)
                num_correct = sum(1 for q in qlist if q.get('correct', 0) > 0)
                mastery = int((num_correct / total) * 100) if total else 0
                console.print(Panel(
                    f"[bold]Progress:[/bold] {num_correct}/{total} correct\n"
                    f"[bold]Mastery Level:[/bold] {mastery}%",
                    title="Your Progress",
                    border_style="cyan"
                ))
            except Exception:
                pass
            
    def _grade_answer_with_ai(self, question_text, user_answer, correct_answer):
        """Using the model to grade the answer relative to the correct answer."""
        if not self.model_handler:
            is_correct = (user_answer.lower() == correct_answer.lower()) or \
                         (difflib.SequenceMatcher(None, user_answer.lower(), correct_answer.lower()).ratio() > 0.8)
            return is_correct, f"The correct answer is: {correct_answer}"

        if correct_answer:
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
        else:
            prompt = (
                f"Task: Evaluate if the student's answer is correct for the given question. Provide specific feedback.\n\n"
                f"Question: {question_text}\n"
                f"Student Answer: {user_answer}\n"
                f"Verdict (Start with [CORRECT] or [INCORRECT]):"
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
                 # If verdict is unclear but valid answer exists, fallback to strict match
                 if correct_answer:
                    is_correct = (user_answer.lower() == correct_answer.lower())
            
            return is_correct, explanation
            
        except Exception as e:
            logger.error(f"AI Grading Error: {e}")
            if correct_answer:
                is_correct = (user_answer.lower() == correct_answer.lower()) or \
                             (difflib.SequenceMatcher(None, user_answer.lower(), correct_answer.lower()).ratio() > 0.8)
                return is_correct, f"The correct answer is: {correct_answer}"
            else:
                return False, "Could not evaluate answer."

            
    @timeit
    def _handle_free_text_question(self, question: str) -> None:
        """Handle free-text questions using the AI model with streaming."""
        try:
             # Ensure model is loaded (lazy check)
            if not self.model_handler.handler.llm:
                self.model_handler.handler.load_model()
            
            # Define stream callback with Live display
            full_answer = ""
            live_display = None
            
            def stream_callback(token):
                nonlocal full_answer, live_display
                full_answer += token
                
                # Initialize Live display on first token to avoid conflict with RAG status logs
                if live_display is None:
                    live_display = Live(
                        Panel(full_answer, title="Answer", border_style="green", padding=(1, 2)),
                        console=console,
                        refresh_per_second=10,
                        transient=False,
                        # auto_refresh=True
                    )
                    live_display.start()
                else:
                    live_display.update(Panel(full_answer, title="Answer", border_style="green", padding=(1, 2)))

            # log_resource_usage("Before model inference")
            
            # Use the RAG engine to query and stream the answer
            try:
                # Remove console.status to prevent layout conflicts with RAG prints and streaming
                response = self.rag_engine.query(
                    query_text=question,
                    subject="",
                    stream_callback=stream_callback
                )
                
            finally:
                # Ensure Live display is stopped properly
                if live_display:
                    live_display.stop()
                elif not full_answer:
                    # If no answer was generated (e.g. error before streaming), handle gracefully
                    pass
            
            answer = response.get('answer', '')
            confidence = response.get('confidence', 0.0)
            relevant_content = response.get('sources', [])
            
            # --- Post-Answer Diagram Generation ---
            try: 
                rag_diagram = response.get('diagram')
                dynamic_diagram_content = generate_diagram_content(
                    question=question,
                    answer=full_answer,
                    grade=self.selected_grade,
                    subject=self.selected_subject
                )
                
                final_diagram = None
                diagram_type = None
                diagram_source = None
                
                if dynamic_diagram_content:
                    final_diagram = dynamic_diagram_content[0]
                    diagram_type = dynamic_diagram_content[1]
                    diagram_source = "Generated"
                elif rag_diagram:
                    final_diagram = rag_diagram
                    diagram_type = 'default'
                    diagram_source = "Knowledge Base"
                
                if final_diagram:
                    # Use rich-based concept-aware rendering
                    from student_app.interface.cli_renderer import CLIRenderer
                    CLIRenderer.render_diagram(
                        diagram_content=final_diagram,
                        diagram_type=diagram_type,
                        source=diagram_source
                    )
            except Exception as diag_e:
                logger.error(f"Diagram generation failed: {diag_e}")

            # --- Confidence & Fallback ---
            confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
            console.print(f"[{confidence_color}]Confidence Score: {confidence:.2f}[/{confidence_color}]")
    
            # Show sources if low confidence
            if confidence < 0.6:
                sources = response.get('sources', [])
                if sources:
                    console.print("\n[dim]Sources used:[/dim]")
                    for s in sources[:2]:
                        console.print(f"[dim]- {s.get('source', 'Unknown')}[/dim]")
                        
            # Ask OpenAI if confidence is low
            if confidence < 0.4:
                console.print("\n[yellow]My confidence is low on this one.[/yellow]")
                if Confirm.ask("Would you like to search online (OpenAI)?"):
                    self._search_with_openai(question)

            # log_resource_usage("After model inference")
            
            # Handle empty or low confidence answers (Last Resort)
            if not answer or (isinstance(answer, str) and len(answer.strip()) == 0):
                console.print(Panel(
                    "I couldn't find a good answer in the database.",
                    title="No Data",
                    border_style="yellow"
                ))
                if relevant_content:
                    console.print("\n📚 Related materials found:")
                    for item in relevant_content[:2]:
                         console.print(f"• {item.get('topic', 'Topic')} - {item.get('concept', 'Concept')}")

        except Exception as e:
            logger.error(f"Error in _handle_free_text_question: {str(e)}")
            console.print(f"[red]Error: {str(e)}[/red]")
            confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
            
            # Add source information if available
            source_display = ""
            if 'source_info' in locals():
                source_display = f"\n[cyan]Source: {source_info}[/cyan]"

            confidence = response.get('confidence', 0.0)
            color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
            console.print(f"[{color}]Confidence Score: {confidence:.2f}[/{color}]")
            
            # Show sources if low confidence
            if confidence < 0.6:
                sources = response.get('sources', [])
                if sources:
                    console.print("\n[dim]Sources used:[/dim]")
                    for s in sources[:2]:
                        console.print(f"[dim]- {s.get('source', 'Unknown')}[/dim]")
        except Exception as e:
            logger.error(f"Error in _handle_free_text_question: {str(e)}")
            console.print(f"[red]Error: {str(e)}[/red]")
            
    def start(self) -> None:
        """Start the CLI interface."""
        try:
            while True:
                # Main menu
                choice = self._create_menu(
                    "Satya Learning System",
                    [
                        "Browse Subjects",
                        "Ask a Question",
                        "Search with OpenAI (Online)",
                        "View Progress",
                        "Export Progress",
                        "Import Progress",
                        "Reset Progress",

                        "Exit"
                    ]
                )
                if choice == "Browse Subjects":
                    self._browse_subjects()
                elif choice == "Ask a Question":
                    self._ask_question()
                elif choice == "Search with OpenAI (Online)":
                    self._search_with_openai()
                elif choice == "View Progress":
                    self._view_progress()
                elif choice == "Export Progress":
                    self._export_progress()
                elif choice == "Import Progress":
                    self._import_progress()
                elif choice == "Reset Progress":
                    self._reset_progress()
                else:
                    if Confirm.ask("Are you sure you want to exit?"):
                        console.print("[bold green]Thank you for using Satya. Goodbye![/bold green]")
                        break
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            
    def _browse_subjects(self) -> None:
        """Browse subjects and their content (grade -> subject -> topic flow)."""
        # 1. Select grade first
        grades = ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
        selected_grade_label = self._create_menu("Select Your Grade", grades)
        self.selected_grade = int(selected_grade_label.split()[-1])  # Extract number
        
        # 2. Get subjects
        subjects = self.content_manager.get_all_subjects()
        if not subjects:
            console.print("[yellow]No subjects available.[/yellow]")
            return
            
        # 3. Select subject
        subject = self._create_menu("Select a Subject", subjects)
        self.selected_subject = subject
        
        # Prefer browseable flattened topic entries (handles nested subtopics)
        browseable_entries = []
        try:
            browseable_entries = self.content_manager.list_browseable_topics(subject)
        except Exception:
            browseable_entries = []
        
        if browseable_entries:
            topic_labels = [e.get("label", e.get("topic", "")) for e in browseable_entries]
            selected_idx, selected_label = self._create_menu_with_index("Select a Topic", topic_labels)
            selected_entry = browseable_entries[selected_idx - 1]
            topic_name = selected_entry["topic"]
            subtopic_path = selected_entry.get("subtopic_path", [])
            # Concepts under chosen path (topic root if path empty)
            concepts = self.content_manager.get_concepts_at_path(subject, topic_name, subtopic_path)
        else:
            # Fallback to legacy topic -> concepts flow
            topics = self.content_manager.get_all_topics(subject)
            if not topics:
                console.print("[yellow]No topics available.[/yellow]")
                return
            topic_name = self._create_menu("Select a Topic", topics)
            concepts = self.content_manager.get_all_concepts(subject, topic_name)
        
        if not concepts:
            console.print("[yellow]No concepts available.[/yellow]")
            return

        concept = self._create_menu(
            "Select a Concept",
            [c["name"] for c in concepts]
        )

        concept_data = next(c for c in concepts if c["name"] == concept)
        self._display_concept(concept_data)

        if concept_data["questions"]:
            if Confirm.ask("Would you like to try some questions?"):
                for question in concept_data["questions"]:
                    self._display_question(
                        question,
                        subject=subject,
                        topic=topic_name,
                        concept=concept,
                        concept_summary=concept_data.get('summary', None)
                    )
                    if not Confirm.ask("Would you like to try another question?"):
                        break
                        
    def _ask_question(self) -> None:
        """Handles free-text questions."""
        subject_completer = WordCompleter(self.content_manager.get_all_subjects())
        
        while True:
            try:
                question = self.session.prompt(
                    "\nAsk any question (or 'back' to return) ",
                    completer=subject_completer
                )
                
                if question.lower() == 'back':
                    break
                    
                self._handle_free_text_question(question)
                
            except Exception as e:
                console.print("[red]Error: Please try again.[/red]")
            
    def _view_progress(self) -> None:
        """View learning progress with summary, mastery, and weak areas."""
        progress = progress_manager.load_progress(self.username)
        if not progress:
            console.print(Panel(
                "You haven't started learning yet! Let's begin your journey! 🚀",
                title="Welcome to Learning!",
                border_style="yellow"
            ))
            return
            
        # Summary stats
        total_questions = 0
        total_attempts = 0
        total_correct = 0
        mastered = set()
        weak = []
        subject_stats = {}
        
        for subject, topics in progress.items():
            subject_stats[subject] = {
                'total': 0,
                'correct': 0,
                'mastered': 0
            }
            for topic, concepts in topics.items():
                for concept, data in concepts.items():
                    for q in data.get('questions', []):
                        total_questions += 1
                        total_attempts += q['attempts']
                        total_correct += q['correct']
                        subject_stats[subject]['total'] += 1
                        subject_stats[subject]['correct'] += q['correct']
                        if q['correct'] >= 3:
                            mastered.add((subject, topic, concept))
                            subject_stats[subject]['mastered'] += 1
                        elif q['attempts'] >= 2 and q['correct'] == 0:
                            weak.append((subject, topic, concept, q['question']))
                            
        # Display overall progress
        CLIRenderer.show_progress_summary(total_questions, total_correct, accuracy, len(mastered))
        
        # Display subject-wise progress
        CLIRenderer.show_subject_progress(subject_stats)
        
        # Areas to improve
        CLIRenderer.show_weak_topics(weak)
            
        # Suggest next concept
        next_concept = self._suggest_next_concept(progress)
        CLIRenderer.show_next_concept_suggestion(next_concept)
            
    def _suggest_next_concept(self, progress):
        """Suggest the next concept to study based on progress."""
        for subject, topics in progress.items():
            for topic, concepts in topics.items():
                for concept, data in concepts.items():
                    all_mastered = all(q['correct'] >= 3 for q in data.get('questions', []))
                    if not all_mastered:
                        return (subject, topic, concept)
        return None

    def _export_progress(self) -> None:
        """Export user progress to a JSON file."""
        progress = progress_manager.load_progress(self.username)
        if not progress:
            console.print("[yellow]No progress to export.[/yellow]")
            return
        filename = Prompt.ask("Enter filename to export progress", default=f"progress_{self.username}_export.json")
        try:
            safe_filename = sanitize_filepath(filename, os.getcwd())
            with open(safe_filename, 'w', encoding='utf-8') as f:
                import json
                json.dump(progress, f, indent=2, ensure_ascii=False)
            log_resource_usage("After progress export")
            console.print(f"[green]Progress exported to {safe_filename}[/green]")
        except Exception as e:
            log_security_event(f"Export failed: {e}")
            console.print(f"[red]Failed to export progress: {e}[/red]")

    def _import_progress(self) -> None:
        """Import user progress from a JSON file."""
        filename = Prompt.ask("Enter filename to import progress from")
        try:
            safe_filename = sanitize_filepath(filename, os.getcwd())
            with open(safe_filename, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
            if not validate_content_input(data):
                log_security_event(f"Rejected import: invalid content from {filename}")
                console.print("[red]Invalid or too large progress file.[/red]")
                return
            progress_manager.save_progress(self.username, data)
            log_resource_usage("After progress import")
            console.print(f"[green]Progress imported from {safe_filename}[/green]")
        except Exception as e:
            log_security_event(f"Import failed: {e}")
            console.print(f"[red]Failed to import progress: {e}[/red]")

    def _reset_progress(self) -> None:
        """Reset user progress after confirmation."""
        if Confirm.ask("Are you sure you want to reset all your progress? This cannot be undone."):
            progress_manager.save_progress(self.username, {})
            log_resource_usage("After progress reset")
            console.print("[green]Progress has been reset.[/green]")

    def _search_with_openai(self) -> None:
        """Prompt the user for a question and search using the OpenAI proxy."""
        while True:
            question = Prompt.ask("Enter your question for OpenAI (or 'back' to return)")
            if question.strip().lower() == 'back':
                break
            with console.status("[bold blue]Contacting OpenAI proxy...[/bold blue]"):
                answer = self.openai_client.ask(question, user_id=self.username)
            console.print(Panel(
                f"[bold blue]{answer}[/bold blue]",
                title="OpenAI Answer (Online)",
                border_style="blue"
            ))

if __name__ == "__main__":
    try:
        content_dir = str(resolve_content_dir("satya_data/content"))
        model_path = str(resolve_model_dir("satya_data/models/phi15"))

        if not os.path.exists(content_dir):
             content_dir = str(resolve_content_dir("scripts/data_collection/data/content"))

        if not os.path.exists(content_dir): 
             raise FileNotFoundError(f"Content directory not found: {content_dir}")
             
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")
            
        cli = CLIInterface(content_dir, model_path)
        cli.start()
    except Exception as e:
        console.print(Panel(
            f"[red]Error initializing application: {str(e)}[/red]",
            title="Fatal Error",
            border_style="red"
        ))
        sys.exit(1) 