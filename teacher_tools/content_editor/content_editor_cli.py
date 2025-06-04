"""
Teacher Content Editor CLI

A command-line interface for teachers to load, edit, and save educational content JSON files for NEBedu.
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

from teacher_tools.content_editor.content_editor_utils import (
    load_content_file, save_content_file, validate_content,
    add_topic, remove_topic, add_concept, remove_concept, add_question, remove_question
)
from system.data_manager.content_manager import ContentManager

console = Console()
style = Style.from_dict({
    'prompt': 'ansicyan bold',
    'input': 'ansigreen',
})

# Patch Confirm.ask for y/n
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

class TeacherContentEditorCLI:
    def __init__(self):
        self.content = None
        self.filepath = None
        self.content_manager = None
        self.session = PromptSession()

    def start(self):
        console.print(Panel("[bold cyan]Welcome to the NEBedu Teacher Content Editor![/bold cyan]", border_style="cyan"))
        while True:
            choice = self._create_menu(
                "Teacher Content Editor Menu",
                [
                    "Load Content File",
                    "List Topics",
                    "Add Topic",
                    "Add Concept",
                    "Add Question",
                    "Remove Topic",
                    "Remove Concept",
                    "Remove Question",
                    "Save Content File",
                    "Exit"
                ]
            )
            if choice == "Load Content File":
                self._load_content()
            elif choice == "List Topics":
                self._list_topics()
            elif choice == "Add Topic":
                self._add_topic()
            elif choice == "Add Concept":
                self._add_concept()
            elif choice == "Add Question":
                self._add_question()
            elif choice == "Remove Topic":
                self._remove_topic()
            elif choice == "Remove Concept":
                self._remove_concept()
            elif choice == "Remove Question":
                self._remove_question()
            elif choice == "Save Content File":
                self._save_content()
            elif choice == "Exit":
                if Confirm.ask("Are you sure you want to exit?"):
                    console.print("[bold green]Thank you for using the Teacher Content Editor. Goodbye![/bold green]")
                    break

    def _create_menu(self, title: str, options: List[str]) -> str:
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
            selected = valid_choices.get(choice.lower())
            if selected:
                return selected
            console.print("[red]Invalid choice. Please enter a number or option text.[/red]")

    def _load_content(self):
        filepath = Prompt.ask("Enter path to content JSON file")
        if not os.path.exists(filepath):
            console.print(f"[red]File not found: {filepath}[/red]")
            return
        try:
            self.content = load_content_file(filepath)
            self.filepath = filepath
            self.content_manager = ContentManager(os.path.dirname(filepath))
            console.print(f"[green]Loaded content from {filepath}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to load content: {e}[/red]")

    def _list_topics(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        topics = self.content.get('topics', [])
        if not topics:
            console.print("[yellow]No topics found.[/yellow]")
            return
        table = Table(title="Topics", show_lines=True)
        table.add_column("Name", style="cyan")
        for topic in topics:
            table.add_row(topic.get('name', ''))
        console.print(table)

    def _add_topic(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        name = Prompt.ask("Enter topic name")
        topic = {"name": name, "subtopics": [], "concepts": []}
        add_topic(self.content, topic)
        console.print(f"[green]Added topic: {name}[/green]")

    def _add_concept(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        topic_name = Prompt.ask("Enter topic name to add concept to")
        subtopic_name = Prompt.ask("Enter subtopic name to add concept to")
        concept_name = Prompt.ask("Enter concept name")
        summary = Prompt.ask("Enter concept summary", default="")
        concept = {"name": concept_name, "summary": summary, "steps": [], "questions": []}
        if add_concept(self.content, topic_name, subtopic_name, concept):
            console.print(f"[green]Added concept: {concept_name}[/green]")
        else:
            console.print(f"[red]Failed to add concept. Check topic and subtopic names.[/red]")

    def _add_question(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        topic_name = Prompt.ask("Enter topic name for question")
        subtopic_name = Prompt.ask("Enter subtopic name for question")
        concept_name = Prompt.ask("Enter concept name for question")
        question_text = Prompt.ask("Enter question text")
        question = {"question": question_text}
        if add_question(self.content, topic_name, subtopic_name, concept_name, question):
            console.print(f"[green]Added question to concept: {concept_name}[/green]")
        else:
            console.print(f"[red]Failed to add question. Check topic, subtopic, and concept names.[/red]")

    def _remove_topic(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        topic_name = Prompt.ask("Enter topic name to remove")
        remove_topic(self.content, topic_name)
        console.print(f"[green]Removed topic: {topic_name}[/green]")

    def _remove_concept(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        topic_name = Prompt.ask("Enter topic name for concept")
        subtopic_name = Prompt.ask("Enter subtopic name for concept")
        concept_name = Prompt.ask("Enter concept name to remove")
        if remove_concept(self.content, topic_name, subtopic_name, concept_name):
            console.print(f"[green]Removed concept: {concept_name}[/green]")
        else:
            console.print(f"[red]Failed to remove concept. Check topic, subtopic, and concept names.[/red]")

    def _remove_question(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        topic_name = Prompt.ask("Enter topic name for question")
        subtopic_name = Prompt.ask("Enter subtopic name for question")
        concept_name = Prompt.ask("Enter concept name for question")
        question_text = Prompt.ask("Enter question text to remove")
        if remove_question(self.content, topic_name, subtopic_name, concept_name, question_text):
            console.print(f"[green]Removed question from concept: {concept_name}[/green]")
        else:
            console.print(f"[red]Failed to remove question. Check topic, subtopic, concept, and question text.[/red]")

    def _save_content(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        if not self.filepath:
            self.filepath = Prompt.ask("Enter path to save content JSON file")
        # Validate before saving
        if self.content_manager and not validate_content(self.content, self.content_manager):
            if not Confirm.ask("Content failed validation. Save anyway?"):
                console.print("[red]Content not saved.[/red]")
                return
        try:
            save_content_file(self.content, self.filepath)
            console.print(f"[green]Content saved to {self.filepath}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to save content: {e}[/red]")

if __name__ == "__main__":
    cli = TeacherContentEditorCLI()
    cli.start() 