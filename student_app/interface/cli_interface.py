"""
CLI Interface Module

This module provides the command-line interface for students to interact with
the NEBedu learning system.
"""

import os
import sys
import logging
import difflib
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings

from system.data_manager.content_manager import ContentManager, get_most_relevant_sentence
from ai_model.model_utils.model_handler import ModelHandler
from student_app.progress import progress_manager
from system.performance.performance_utils import timeit, log_resource_usage
from system.security.security_utils import validate_username, sanitize_filepath, log_security_event, validate_content_input
from student_app.learning.openai_proxy_client import OpenAIProxyClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('satya.log'),  # Log to file instead of console
        logging.StreamHandler()  # Also log to console for debugging
    ]
)
logger = logging.getLogger(__name__)

# Configure rich console
console = Console()

# Configure prompt_toolkit styles
style = Style.from_dict({
    'prompt': 'ansicyan bold',
    'input': 'ansigreen',
})

# Configure key bindings
bindings = KeyBindings()

@bindings.add('h')
def _(event):
    """Show help when 'h' is pressed."""
    event.app.current_buffer.insert_text('help')

@bindings.add('q')
def _(event):
    """Exit when 'q' is pressed."""
    event.app.current_buffer.insert_text('exit')

# Patch Confirm.ask to always accept y/n/yes/no (case-insensitive) and show clear prompt
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
        self.content_manager = ContentManager(content_dir)
        
        # Ensure model path exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")
            
        # Initialize model handler with proper path
        try:
            self.model_handler = ModelHandler(model_path)
            # Pre-load the model to catch any initialization errors
            self.model_handler.phi2_handler.load_model()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            console.print(Panel(
                "[red]Error: Could not initialize the AI model. Please check the model files and try again.[/red]",
                title="Model Error",
                border_style="red"
            ))
            raise
            
        self.session = PromptSession(key_bindings=bindings)
        self.username = self._prompt_username()
        self._show_welcome_message()
        self._show_model_info()
        # Configure OpenAI proxy client with environment variables or defaults
        proxy_url = os.getenv("OPENAI_PROXY_URL")
        proxy_api_key = os.getenv("OPENAI_PROXY_KEY")
        self.openai_client = OpenAIProxyClient(proxy_url=proxy_url, api_key=proxy_api_key)
        
    def _show_welcome_message(self) -> None:
        """Display welcome message and quick start guide."""
        welcome_text = """
        # Welcome to Satya Learning System! 👋

## Quick Start Guide
- Press 'h' key anytime for help
- Press 'q' key to exit
- Use numbers or type menu options
- Type 'back' to return to previous menu

## Available Features
1. 📚 Browse Subjects - Study organized content
2. ❓ Ask Questions - Get AI-powered answers
3. 📊 View Progress - Track your learning
4. 💾 Export Progress - Save your progress
5. 📥 Import Progress - Load saved progress
6. 🔄 Reset Progress - Start fresh

## Tips
- Take your time to understand concepts
- Use hints when stuck
- Review explanations for better understanding
- Track your progress regularly
"""
        console.print(Panel(Markdown(welcome_text), title="Welcome!", border_style="cyan"))
        
    def _show_help(self, context: str = "main") -> None:
        """Display context-specific help."""
        help_texts = {
            "main": """
# Main Menu Help
- [cyan]Browse Subjects[/cyan]: Study organized content by subject, topic, and concept
- [cyan]Ask Questions[/cyan]: Get AI-powered answers to your questions
- [cyan]View Progress[/cyan]: See your learning statistics and areas to improve
- [cyan]Export/Import Progress[/cyan]: Save or load your learning progress
- [cyan]Reset Progress[/cyan]: Start fresh (use with caution)

Press [cyan]h[/cyan] anytime for help, [cyan]q[/cyan] to exit
""",
            "browse": """
# Browse Subjects Help
- Select a subject to see available topics
- Choose a topic to view concepts
- Study concepts and try practice questions
- Use hints when stuck
- Review explanations for better understanding

Type 'back' to return to previous menu
""",
            "question": """
# Ask Questions Help
- Type your question in natural language
- Get AI-powered answers with confidence scores
- Request hints for better understanding
- Ask follow-up questions
- Type 'back' to return to main menu
""",
            "progress": """
# Progress Tracking Help
- View your overall learning statistics
- See mastered concepts and weak areas
- Get personalized learning suggestions
- Export progress to save your work
- Import progress to continue learning
"""
        }
        
        help_text = help_texts.get(context, help_texts["main"])
        console.print(Panel(Markdown(help_text), title="Help", border_style="cyan"))
        
    def _show_model_info(self) -> None:
        """Display information about the current AI model."""
        try:
            model_info = self.model_handler.get_model_info()
            if not model_info:
                raise ValueError("No model information available")
                
            console.print(Panel(
                f"[bold cyan]Current AI Model:[/bold cyan] {model_info.get('name', 'Phi-2')}\n"
                f"[bold]Version:[/bold] {model_info.get('version', '1.0')}\n"
                f"[bold]Quantization:[/bold] {model_info.get('quantization', 'Q4_K_M')}\n"
                f"[bold]Context Size:[/bold] {model_info.get('context_size', 2048)}\n"
                f"[bold]Threads:[/bold] {model_info.get('threads', 4)}\n"
                f"[bold]Temperature:[/bold] {model_info.get('temperature', 0.7)}\n"
                f"[bold]Top P:[/bold] {model_info.get('top_p', 0.9)}",
                title="AI Model Information",
                border_style="cyan"
            ))
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            console.print(Panel(
                "[yellow]Could not retrieve model information. The model may not be properly loaded.[/yellow]",
                title="Model Warning",
                border_style="yellow"
            ))
        
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
        """
        Create and display a menu.
        
        Args:
            title (str): Menu title
            options (List[str]): List of options
            
        Returns:
            str: Selected option
        """
        table = Table(title=title, show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="green")
        
        for i, option in enumerate(options, 1):
            table.add_row(str(i), option)
            
        console.print(table)
        console.print("\nPress 'h' for help, 'q' to exit")
        
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
            
    def _display_concept(self, concept: Dict[str, Any]) -> None:
        """
        Display a concept and its content.
        
        Args:
            concept (Dict[str, Any]): Concept data
        """
        console.print(Panel(
            f"[bold cyan]{concept.get('name', 'Concept')}[/bold cyan]\n\n"
            f"[green]{concept.get('summary', '')}[/green]",
            title="Concept",
            border_style="cyan"
        ))
        
        # Show learning objectives if available
        if 'objectives' in concept:
            console.print("\n[bold yellow]Learning Objectives:[/bold yellow]")
            for i, objective in enumerate(concept['objectives'], 1):
                console.print(f"{i}. {objective}")
                
        # Show key points if available
        if 'key_points' in concept:
            console.print("\n[bold yellow]Key Points:[/bold yellow]")
            for point in concept['key_points']:
                console.print(f"• {point}")
                
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
            
        # Get user's answer with progress indicator
        with console.status("[bold green]Thinking...[/bold green]"):
            answer = Prompt.ask("Your answer")
        
        # Check answer with visual feedback
        correct = any(ans.lower() in answer.lower() for ans in question.get('acceptable_answers', []))
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
                        
        # Show explanation with better formatting
        if Confirm.ask("Would you like to see the explanation?"):
            explanation = question.get('explanation')
            if not explanation and concept_summary:
                explanation = concept_summary
            if not explanation:
                explanation = 'No explanation available.'
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
            
            # Show progress update
            progress = progress_manager.get_concept_progress(
                self.username, subject, topic, concept
            )
            if progress:
                console.print(Panel(
                    f"[bold]Progress:[/bold] {progress['correct']}/{progress['total']} correct\n"
                    f"[bold]Mastery Level:[/bold] {progress['mastery_level']}%",
                    title="Your Progress",
                    border_style="cyan"
                ))
            
    @timeit
    def _handle_free_text_question(self, question: str) -> None:
        """Handle free-text questions using the AI model."""
        try:
            # Ensure model is loaded
            if not self.model_handler.phi2_handler.llm:
                self.model_handler.phi2_handler.load_model()
                
            with console.status("[bold green]Thinking...[/bold green]"):
                log_resource_usage("Before model inference")
                
                # First try to find relevant content
                try:
                    relevant_content = self.content_manager.search_content(question)
                    if relevant_content:
                        # Get the full concept data to access questions and answers
                        subject = relevant_content[0]['subject']
                        topic = relevant_content[0]['topic']
                        concept = relevant_content[0]['concept']
                        concept_data = self.content_manager.get_concept(subject, topic, concept)
                        
                        if concept_data and 'questions' in concept_data:
                            # Try to find a matching question
                            for q in concept_data['questions']:
                                if isinstance(q, dict) and 'question' in q:
                                    # Use fuzzy matching to find similar questions
                                    if difflib.SequenceMatcher(None, q['question'].lower(), question.lower()).ratio() > 0.6:
                                        # Found a matching question, use its answer
                                        if 'acceptable_answers' in q and q['acceptable_answers']:
                                            answer = q['acceptable_answers'][0]
                                            confidence = 0.9  # High confidence since it's from our content
                                            # Use the question's hints if available
                                            hints = q.get('hints', [])
                                            break
                            else:
                                # No matching question found, use the summary
                                summary = relevant_content[0]['summary']
                                context = get_most_relevant_sentence(summary, question)
                                logger.info(f"Using focused context: {context}")
                                try:
                                    answer, confidence = self.model_handler.get_answer(question, context)
                                    if not answer or len(answer.strip()) == 0:
                                        raise ValueError("Model generated empty answer")
                                except Exception as e:
                                    logger.error(f"Model inference error: {str(e)}")
                                    console.print(Panel(
                                        "I'm having trouble generating an answer. Let me show you the relevant content instead:",
                                        title="Model Error",
                                        border_style="yellow"
                                    ))
                                    answer = context
                                    confidence = 0.8
                        else:
                            # No questions found, use the summary
                            summary = relevant_content[0]['summary']
                            context = get_most_relevant_sentence(summary, question)
                            logger.info(f"Using focused context: {context}")
                            try:
                                answer, confidence = self.model_handler.get_answer(question, context)
                                if not answer or len(answer.strip()) == 0:
                                    raise ValueError("Model generated empty answer")
                            except Exception as e:
                                logger.error(f"Model inference error: {str(e)}")
                                console.print(Panel(
                                    "I'm having trouble generating an answer. Let me show you the relevant content instead:",
                                    title="Model Error",
                                    border_style="yellow"
                                ))
                                answer = context
                                confidence = 0.8
                    else:
                        # Use default context from content manager
                        context = self.content_manager.get_default_context()
                        console.print(Panel(
                            "I couldn't find a direct match in your study materials, but I'll try to answer using general knowledge.",
                            title="AI Attempt",
                            border_style="yellow"
                        ))
                        try:
                            answer, confidence = self.model_handler.get_answer(question, context)
                            if not answer or len(answer.strip()) == 0:
                                raise ValueError("Model generated empty answer")
                        except Exception as e:
                            logger.error(f"Model inference error: {str(e)}")
                            console.print(Panel(
                                "I'm having trouble generating an answer. Please try rephrasing your question or ask about a specific topic.",
                                title="Model Error",
                                border_style="yellow"
                            ))
                            return
                except Exception as e:
                    logger.error(f"Error searching content: {str(e)}")
                    console.print("[red]Error searching content. Please try again.[/red]")
                    return
                
                log_resource_usage("After model inference")
                
            # Handle empty or low confidence answers
            if not answer or confidence < 0.1 or (isinstance(answer, str) and len(answer.strip()) == 0):
                console.print(Panel(
                    "I'm not sure about that. Let me help you find the right information:",
                    title="Learning Opportunity",
                    border_style="yellow"
                ))
                if relevant_content:
                    console.print("\n📚 Here's what I found in your study materials:")
                    for item in relevant_content:
                        console.print(Panel(
                            f"Subject: {item['subject']}\n"
                            f"Topic: {item['topic']}\n"
                            f"Concept: {item['concept']}\n"
                            f"Summary: {item['summary']}",
                            border_style="green"
                        ))
                return
                
            # Display answer with confidence indicator
            confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
            console.print(Panel(
                f"[bold]{answer}[/bold]\n\n"
                f"[{confidence_color}]Confidence: {confidence:.1%}[/{confidence_color}]",
                title="Answer",
                border_style="green"
            ))

            # Offer to ask OpenAI if confidence is low or on user request
            if confidence < 0.7:
                if Confirm.ask("Would you like to ask OpenAI (online) for another answer?"):
                    with console.status("[bold blue]Contacting OpenAI proxy...[/bold blue]"):
                        openai_answer = self.openai_client.ask(question, user_id=self.username)
                    console.print(Panel(
                        f"[bold blue]{openai_answer}[/bold blue]",
                        title="OpenAI Answer (Online)",
                        border_style="blue"
                    ))

            # Show hints
            try:
                if 'hints' in locals() and hints:
                    # Use the hints from the matching question
                    console.print("\n💡 Here are some hints to help you understand better:")
                    for hint in hints:
                        console.print(f"• {hint}")
                else:
                    # Generate hints using the model
                    hint_context = relevant_content[0]['summary'] if relevant_content else context
                    hints = self.model_handler.get_hints(question, hint_context)
                    if hints:
                        console.print("\n💡 Here are some hints to help you understand better:")
                        for hint in hints:
                            console.print(f"• {hint}")
                    else:
                        console.print("\n💡 Sorry, no hints are available for this question.")
            except Exception as e:
                logger.error(f"Error generating hints: {str(e)}")
                console.print("\n💡 Sorry, no hints are available for this question.")
            
            # Show related concepts
            if len(relevant_content) > 1:
                console.print("\n📚 Related concepts you might want to study:")
                for item in relevant_content[1:3]:  # Show up to 2 additional related concepts
                    console.print(Panel(
                        f"Subject: {item['subject']}\n"
                        f"Topic: {item['topic']}\n"
                        f"Concept: {item['concept']}",
                        border_style="blue"
                    ))
                    
        except Exception as e:
            logger.error(f"Error in _handle_free_text_question: {str(e)}")
            console.print(Panel(
                "[red]I'm having trouble processing your question. Please try again.[/red]",
                title="Error",
                border_style="red"
            ))
        finally:
            # Clean up model resources
            try:
                self.model_handler.phi2_handler.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up model: {str(e)}")
            
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
                        "Switch Model",
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
                elif choice == "Switch Model":
                    self._switch_model()
                else:
                    if Confirm.ask("Are you sure you want to exit?"):
                        console.print("[bold green]Thank you for using Satya. Goodbye![/bold green]")
                        break
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            
    def _browse_subjects(self) -> None:
        """Browse subjects and their content."""
        # Get subjects
        subjects = self.content_manager.get_all_subjects()
        if not subjects:
            console.print("[yellow]No subjects available.[/yellow]")
            return
            
        # Select subject
        subject = self._create_menu("Select a Subject", subjects)
        
        # Get topics
        topics = self.content_manager.get_all_topics(subject)
        if not topics:
            console.print("[yellow]No topics available.[/yellow]")
            return
            
        # Select topic
        topic = self._create_menu("Select a Topic", topics)
        
        # Get concepts
        concepts = self.content_manager.get_all_concepts(subject, topic)
        if not concepts:
            console.print("[yellow]No concepts available.[/yellow]")
            return
            
        # Select concept
        concept = self._create_menu(
            "Select a Concept",
            [c["name"] for c in concepts]
        )
        
        # Display concept
        concept_data = next(c for c in concepts if c["name"] == concept)
        self._display_concept(concept_data)
        
        # Handle questions
        if concept_data["questions"]:
            if Confirm.ask("Would you like to try some questions?"):
                for question in concept_data["questions"]:
                    self._display_question(
                        question,
                        subject=subject,
                        topic=topic,
                        concept=concept,
                        concept_summary=concept_data.get('summary', None)
                    )
                    if not Confirm.ask("Would you like to try another question?"):
                        break
                        
    def _ask_question(self) -> None:
        """Handle free-text questions."""
        # Create a word completer for subjects
        subject_completer = WordCompleter(self.content_manager.get_all_subjects())
        
        while True:
            try:
                # Use prompt_toolkit's session with completer
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
                            
        accuracy = (total_correct / total_attempts * 100) if total_attempts else 0
        
        # Display overall progress with encouraging message
        if accuracy >= 80:
            message = "Excellent work! Keep up the great learning! 🌟"
        elif accuracy >= 60:
            message = "Good progress! You're on the right track! 💪"
        else:
            message = "Keep practicing! Every question helps you learn! 📚"
            
        console.print(Panel(
            f"{message}\n\n"
            f"📝 Questions Answered: {total_questions}\n"
            f"✅ Correct Answers: {total_correct}\n"
            f"🎯 Your Score: {accuracy:.1f}%\n"
            f"🏆 Concepts Mastered: {len(mastered)}",
            title="Your Learning Journey",
            border_style="cyan"
        ))
        
        # Display subject-wise progress with simple progress bars
        console.print("\n📚 Your Progress in Each Subject:")
        for subject, stats in subject_stats.items():
            # Calculate progress percentage
            progress_pct = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            # Create a simple progress bar
            progress_bar = "■" * int(progress_pct / 10) + "□" * (10 - int(progress_pct / 10))
            
            # Add encouraging message based on progress
            if progress_pct >= 80:
                status = "🌟 Excellent!"
            elif progress_pct >= 60:
                status = "💪 Good!"
            else:
                status = "📚 Keep Learning!"
                
            console.print(Panel(
                f"{subject}:\n"
                f"Progress: {progress_bar} {progress_pct:.1f}%\n"
                f"Mastered: {stats['mastered']} concepts\n"
                f"Status: {status}",
                border_style="green"
            ))
        
        # Areas to improve
        if weak:
            console.print("\n📌 Topics to Review:")
            for s, t, c, q in weak:
                console.print(Panel(
                    f"Subject: {s}\n"
                    f"Topic: {t}\n"
                    f"Concept: {c}\n"
                    f"Question: {q}",
                    border_style="yellow"
                ))
            
        # Suggest next concept with encouraging message
        next_concept = self._suggest_next_concept(progress)
        if next_concept:
            s, t, c = next_concept
            console.print(Panel(
                f"Ready for your next challenge? 🎯\n\n"
                f"Try learning about: {c}\n"
                f"in {t} ({s})",
                title="Keep Learning!",
                border_style="green"
            ))
            
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

    def _switch_model(self) -> None:
        """Switch between available AI models."""
        try:
            # Get available models
            available_models = self.model_handler.get_available_models()
            if not available_models:
                console.print("[yellow]No other models available.[/yellow]")
                return

            # Show current model
            current_model = self.model_handler.get_model_info()['name']
            console.print(f"\n[bold]Current Model:[/bold] {current_model}")

            # Create menu for model selection
            model_choice = self._create_menu(
                "Select a Model",
                available_models
            )

            # Switch to selected model
            if Confirm.ask(f"Switch to {model_choice}?"):
                self.model_handler.switch_model(model_choice)
                console.print(f"[green]Switched to {model_choice}[/green]")
                self._show_model_info()
        except Exception as e:
            logger.error(f"Error switching model: {str(e)}")
            console.print("[red]Failed to switch model. Please try again.[/red]")

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
        # Use absolute paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        content_dir = os.path.join(base_dir, "scripts", "data_collection", "data", "content")
        model_path = os.path.join(base_dir, "ai_model", "exported_model")
        
        # Verify paths exist
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