# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Teacher Content Editor CLI

A command-line interface for teachers to load, edit, and save educational content JSON files for Satya.
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
        self.current_subject = None
        self.content_manager = ContentManager()
        self.session = PromptSession()

    def start(self):
        console.print(Panel("[bold cyan]Welcome to the Satya Teacher Content Editor![/bold cyan]", border_style="cyan"))
        while True:
            if self.current_subject:
                console.print(Panel(f"[bold green]Current Subject: {self.current_subject}[/bold green]", border_style="green"))

            load_option = "Switch Subject" if self.content else "Load Subject Content"
            options = [load_option]
            
            default_choice = "1"
            
            if self.content:
                options.extend([
                    "List Topics",
                    "Add Topic",
                    "Add Concept",
                    "Add Question",
                    "Remove Topic",
                    "Remove Concept",
                    "Remove Question",
                    "Save Content"
                ])
                default_choice = "2"
            
            options.append("Exit")

            choice = self._create_menu("Teacher Content Editor Menu", options, default_choice)
            
            if choice == "Load Subject Content" or choice == "Switch Subject":
                self._load_subject_content()
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
            elif choice == "Save Content":
                self._save_content()
            elif choice == "Exit":
                if Confirm.ask("Are you sure you want to exit?"):
                    console.print("[bold green]Thank you for using the Teacher Content Editor. Goodbye![/bold green]")
                    break

    def _create_menu(self, title: str, options: List[str], default_choice: str = "1") -> str:
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
                default=default_choice
            )
            selected = valid_choices.get(choice.lower())
            if selected:
                return selected
            console.print("[red]Invalid choice. Please enter a number or option text.[/red]")

    def _load_subject_content(self):
        subjects = self.content_manager.get_all_subjects()
        if not subjects:
            console.print("[yellow]No subjects found in Content Manager.[/yellow]")
            return
        
        console.print("\n[bold]Available Subjects:[/bold]")
        for i, subj in enumerate(subjects, 1):
            console.print(f"{i}. {subj}")
            
        choice = Prompt.ask("Enter subject name", choices=subjects)
        
        try:
            self.content = self.content_manager.get_subject(choice)
            self.current_subject = choice
            console.print(f"[green]Loaded content for subject: {choice}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to load content for {choice}: {e}[/red]")

    def _list_topics(self):
        if not self.content:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        topics = self.content.get('topics', [])
        if not topics:
            console.print("[yellow]No topics found.[/yellow]")
            return
        table = Table(title=f"Topics in {self.current_subject}", show_lines=True)
        table.add_column("Name", style="cyan")
        table.add_column("Subtopics", style="magenta")
        table.add_column("Concepts", style="green")
        
        for topic in topics:
            sub_count = len(topic.get('subtopics', []))
            conc_count = len(topic.get('concepts', []))
            table.add_row(topic.get('name', ''), str(sub_count), str(conc_count))
        console.print(table)

    def _add_topic(self):
        if not self.content:
            return
        name = Prompt.ask("Enter topic name")
        topic = {"name": name, "subtopics": [], "concepts": []}
        add_topic(self.content, topic)
        console.print(f"[green]Added topic: {name}[/green]")

    def _add_concept(self):
        if not self.content:
            return
        topic_name = Prompt.ask("Enter topic name to add concept to")
        subtopic_name = Prompt.ask("Enter subtopic name (optional, press Enter to skip)", default="")
        if not subtopic_name:
            subtopic_name = topic_name

        concept_name = Prompt.ask("Enter concept name")
        summary = Prompt.ask("Enter concept summary", default="")
        concept = {"name": concept_name, "summary": summary, "steps": [], "questions": []}
        
        if add_concept(self.content, topic_name, subtopic_name, concept):
            console.print(f"[green]Added concept: {concept_name}[/green]")
        else:
            console.print(f"[red]Failed to add concept. Topic '{topic_name}' or subtopic '{subtopic_name}' not found.[/red]")

    def _add_question(self):
        if not self.content:
            return
        topic_name = Prompt.ask("Enter topic name")
        subtopic_name = Prompt.ask("Enter subtopic name (optional)", default="")
        if not subtopic_name: subtopic_name = topic_name

        concept_name = Prompt.ask("Enter concept name")
        question_text = Prompt.ask("Enter question text")
        question = {"question": question_text}
        
        if add_question(self.content, topic_name, subtopic_name, concept_name, question):
            console.print(f"[green]Added question to concept: {concept_name}[/green]")
        else:
            console.print(f"[red]Failed to add question. Check path.[/red]")

    def _remove_topic(self):
        if not self.content:
            return
        topic_name = Prompt.ask("Enter topic name to remove")
        if Confirm.ask(f"Are you sure you want to delete topic '{topic_name}'?"):
            remove_topic(self.content, topic_name)
            console.print(f"[green]Removed topic: {topic_name}[/green]")

    def _remove_concept(self):
        if not self.content:
            return
        topic_name = Prompt.ask("Enter topic name")
        subtopic_name = Prompt.ask("Enter subtopic name (optional)", default="")
        if not subtopic_name: subtopic_name = topic_name
        
        concept_name = Prompt.ask("Enter concept name to remove")
        if Confirm.ask(f"Delete concept '{concept_name}'?"):
            if remove_concept(self.content, topic_name, subtopic_name, concept_name):
                console.print(f"[green]Removed concept: {concept_name}[/green]")
            else:
                console.print("[red]Concept not found.[/red]")

    def _remove_question(self):
        if not self.content:
            return
        topic_name = Prompt.ask("Enter topic name")
        subtopic_name = Prompt.ask("Enter subtopic name (optional)", default="")
        if not subtopic_name: subtopic_name = topic_name
        
        concept_name = Prompt.ask("Enter concept name")
        question_text = Prompt.ask("Enter question text to remove")
        
        if remove_question(self.content, topic_name, subtopic_name, concept_name, question_text):
            console.print(f"[green]Removed question.[/green]")
        else:
            console.print("[red]Question not found.[/red]")

    def _save_content(self):
        if not self.content or not self.current_subject:
            console.print("[yellow]No content loaded.[/yellow]")
            return
        
        try:
            self.content_manager.update_content(self.current_subject, self.content)
            console.print(f"[bold green]Successfully saved content for {self.current_subject}![/bold green]")
            console.print(f"[dim]Backup created in {self.current_subject}/backups[/dim]")
        except Exception as e:
            console.print(f"[red]Failed to save content: {e}[/red]")
            if Confirm.ask("Try saving to a local file instead?"):
                fname = f"{self.current_subject}_emergency_save.json"
                try:
                    save_content_file(self.content, fname)
                    console.print(f"[green]Saved to {fname}[/green]")
                except Exception as e2:
                    console.print(f"[red]Emergency save failed: {e2}[/red]")

if __name__ == "__main__":
    cli = TeacherContentEditorCLI()
    cli.start() 