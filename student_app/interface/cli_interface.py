"""
CLI Interface Module

This module provides the command-line interface for students to interact with
the NEBedu learning system.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from system.data_manager.content_manager import ContentManager
from ai_model.model_utils.model_handler import ModelHandler
from student_app.progress import progress_manager
from system.performance.performance_utils import timeit, log_resource_usage
from system.security.security_utils import validate_username, sanitize_filepath, log_security_event, validate_content_input

# Configure rich console
console = Console()

# Configure prompt_toolkit styles
style = Style.from_dict({
    'prompt': 'ansicyan bold',
    'input': 'ansigreen',
})

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
    Command-line interface for the NEBedu learning system.
    
    Attributes:
        content_manager (ContentManager): Manager for educational content
        model_handler (ModelHandler): Handler for AI model
        session (PromptSession): Interactive prompt session
        username (str): The entered username
    """
    
    def __init__(self, content_dir: str, model_path: str):
        """
        Initialize the CLI interface.
        
        Args:
            content_dir (str): Path to content directory
            model_path (str): Path to model directory
        """
        self.content_manager = ContentManager(content_dir)
        self.model_handler = ModelHandler(model_path)
        self.session = PromptSession()
        self.username = self._prompt_username()
        
    def _prompt_username(self) -> str:
        """
        Prompt the user for a username at the start of the session.
        Returns:
            str: The entered username
        """
        while True:
            username = Prompt.ask("Enter your username (for progress tracking)", default="student")
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
        
        valid_choices = {str(i): opt for i, opt in enumerate(options, 1)}
        valid_choices.update({opt.lower(): opt for opt in options})
        while True:
            choice = Prompt.ask(
                "Select an option (number or text)",
                choices=list(valid_choices.keys()),
                default="1"
            )
            # Accept both number and text
            selected = valid_choices.get(choice.lower())
            if selected:
                return selected
            console.print("[red]Invalid choice. Please enter a number or option text.[/red]")
            
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
        console.print(Panel(
            f"[bold yellow]{question['question']}[/bold yellow]",
            title="Question",
            border_style="yellow"
        ))
        
        # Get user's answer
        answer = Prompt.ask("Your answer")
        
        # Check answer
        correct = any(ans.lower() in answer.lower() for ans in question.get('acceptable_answers', []))
        if correct:
            console.print("[green]Correct![/green]")
        else:
            console.print("[red]Not quite right.[/red]")
            
            # Offer hints
            if Confirm.ask("Would you like a hint?"):
                for hint in question.get('hints', []):
                    console.print(f"[yellow]Hint:[/yellow] {hint}")
                    if not Confirm.ask("Would you like another hint?"):
                        break
                        
        # Show explanation
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
            
        # Update progress after question attempt
        if subject and topic and concept:
            progress_manager.update_progress(
                self.username, subject, topic, concept, question['question'], correct
            )
            
    @timeit
    def _handle_free_text_question(self, question: str) -> None:
        """
        Handle a free-text question using the AI model.
        Args:
            question (str): User's question
        """
        try:
            log_resource_usage("Before model inference")
            # Get answer from model
            answer, confidence = self.model_handler.get_answer(
                question,
                "A computer is an electronic device that processes data."
            )
            log_resource_usage("After model inference")
            # Display answer
            console.print(Panel(
                f"[bold green]{answer}[/bold green]\n\n"
                f"Confidence: {confidence:.2%}",
                title="AI Answer",
                border_style="green"
            ))
            # Offer hints
            if Confirm.ask("Would you like some hints to understand better?"):
                hints = self.model_handler.get_hints(question, answer)
                for hint in hints:
                    console.print(f"[yellow]Hint:[/yellow] {hint}")
                    if not Confirm.ask("Would you like another hint?"):
                        break
        except Exception as e:
            log_security_event(f"Model inference error: {e}")
            console.print(f"[red]Error: {str(e)}[/red]")
            
    def start(self) -> None:
        """Start the CLI interface."""
        try:
            while True:
                # Main menu
                choice = self._create_menu(
                    "NEBedu Learning System",
                    [
                        "Browse Subjects",
                        "Ask a Question",
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
                        console.print("[bold green]Thank you for using NEBedu. Goodbye![/bold green]")
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
        while True:
            question = Prompt.ask(
                "\nAsk any question (or 'back' to return)",
                completer=WordCompleter(self.content_manager.get_all_subjects())
            )
            
            if question.lower() == 'back':
                break
                
            self._handle_free_text_question(question)
            
    def _view_progress(self) -> None:
        """View learning progress with summary, mastery, and weak areas."""
        progress = progress_manager.load_progress(self.username)
        if not progress:
            console.print("[yellow]No progress found for this user.[/yellow]")
            return
        # Summary stats
        total_questions = 0
        total_attempts = 0
        total_correct = 0
        mastered = set()
        weak = []
        for subject, topics in progress.items():
            for topic, concepts in topics.items():
                for concept, data in concepts.items():
                    for q in data.get('questions', []):
                        total_questions += 1
                        total_attempts += q['attempts']
                        total_correct += q['correct']
                        if q['correct'] >= 3:
                            mastered.add((subject, topic, concept))
                        elif q['attempts'] >= 2 and q['correct'] == 0:
                            weak.append((subject, topic, concept, q['question']))
        accuracy = (total_correct / total_attempts * 100) if total_attempts else 0
        console.print(Panel(f"[bold]Total Questions Attempted:[/bold] {total_questions}\n"
                            f"[bold]Total Attempts:[/bold] {total_attempts}\n"
                            f"[bold]Total Correct:[/bold] {total_correct}\n"
                            f"[bold]Accuracy:[/bold] {accuracy:.1f}%\n"
                            f"[bold]Concepts Mastered:[/bold] {len(mastered)}",
                            title="Progress Summary", border_style="cyan"))
        # Weak areas
        if weak:
            table = Table(title="Areas to Review", show_lines=True)
            table.add_column("Subject", style="cyan")
            table.add_column("Topic", style="magenta")
            table.add_column("Concept", style="green")
            table.add_column("Question", style="yellow")
            for s, t, c, q in weak:
                table.add_row(s, t, c, q)
            console.print(table)
        # Full progress table
        table = Table(title=f"Progress for {self.username}")
        table.add_column("Subject", style="cyan")
        table.add_column("Topic", style="magenta")
        table.add_column("Concept", style="green")
        table.add_column("Question", style="yellow")
        table.add_column("Attempts", style="white")
        table.add_column("Correct", style="green")
        table.add_column("Mastered", style="bold green")
        for subject, topics in progress.items():
            for topic, concepts in topics.items():
                for concept, data in concepts.items():
                    for q in data.get('questions', []):
                        mastered_flag = "✅" if q['correct'] >= 3 else ""
                        table.add_row(
                            subject,
                            topic,
                            concept,
                            q['question'],
                            str(q['attempts']),
                            str(q['correct']),
                            mastered_flag
                        )
        console.print(table)
        # Suggest next concept
        next_concept = self._suggest_next_concept(progress)
        if next_concept:
            s, t, c = next_concept
            console.print(Panel(f"[bold]Suggested Next Concept:[/bold] {c} (Topic: {t}, Subject: {s})",
                                title="Keep Learning!", border_style="green"))

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

if __name__ == "__main__":
    # You may want to make these configurable or use argparse in the future
    content_dir = "scripts/data_collection/data/content"
    model_path = "ai_model/exported_model"
    cli = CLIInterface(content_dir, model_path)
    cli.start() 