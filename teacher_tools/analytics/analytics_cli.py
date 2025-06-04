"""
Teacher Analytics CLI

A command-line interface for teachers to generate and export student/class analytics reports for NEBedu.
"""

import os
from typing import List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from teacher_tools.analytics.analytics_utils import (
    generate_student_report, export_report_csv, export_report_json
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

class TeacherAnalyticsCLI:
    def __init__(self):
        self.content_manager = None
        self.session = PromptSession()

    def start(self):
        console.print(Panel("[bold cyan]Welcome to the NEBedu Teacher Analytics CLI![/bold cyan]", border_style="cyan"))
        self._load_content_manager()
        while True:
            choice = self._create_menu(
                "Teacher Analytics Menu",
                [
                    "Generate Student Report",
                    "Generate Class Report",
                    "Exit"
                ]
            )
            if choice == "Generate Student Report":
                self._student_report()
            elif choice == "Generate Class Report":
                self._class_report()
            elif choice == "Exit":
                if Confirm.ask("Are you sure you want to exit?"):
                    console.print("[bold green]Thank you for using the Teacher Analytics CLI. Goodbye![/bold green]")
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

    def _load_content_manager(self):
        content_dir = Prompt.ask("Enter path to content directory", default="data/content")
        if not os.path.exists(content_dir):
            console.print(f"[red]Content directory not found: {content_dir}[/red]")
            exit(1)
        self.content_manager = ContentManager(content_dir)
        console.print(f"[green]Loaded content from {content_dir}[/green]")

    def _student_report(self):
        username = Prompt.ask("Enter student username")
        try:
            report = generate_student_report(username, self.content_manager)
            self._display_student_report(report)
            self._export_report(report, username)
        except Exception as e:
            console.print(f"[red]Failed to generate report: {e}[/red]")

    def _display_student_report(self, report):
        table = Table(title=f"Student Report: {report['username']}", show_lines=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total Questions", str(report["total_questions"]))
        table.add_row("Total Attempts", str(report["total_attempts"]))
        table.add_row("Total Correct", str(report["total_correct"]))
        table.add_row("Mastered Concepts", str(report["mastered_concepts"]))
        table.add_row("Weak Concepts", str(len(report["weak_concepts"])))
        console.print(table)
        if report["weak_concepts"]:
            wc_table = Table(title="Weak Concepts", show_lines=True)
            wc_table.add_column("Subject", style="cyan")
            wc_table.add_column("Topic", style="magenta")
            wc_table.add_column("Concept", style="yellow")
            wc_table.add_column("Question", style="white")
            for wc in report["weak_concepts"]:
                wc_table.add_row(wc["subject"], wc["topic"], wc["concept"], wc["question"])
            console.print(wc_table)

    def _export_report(self, report, username):
        if Confirm.ask("Export report as CSV?"):
            filename = Prompt.ask("Enter CSV filename", default=f"{username}_report.csv")
            export_report_csv(report, filename)
            console.print(f"[green]Report exported to {filename}[/green]")
        if Confirm.ask("Export report as JSON?"):
            filename = Prompt.ask("Enter JSON filename", default=f"{username}_report.json")
            export_report_json(report, filename)
            console.print(f"[green]Report exported to {filename}[/green]")

    def _class_report(self):
        usernames_str = Prompt.ask("Enter student usernames (comma-separated)")
        usernames = [u.strip() for u in usernames_str.split(",") if u.strip()]
        if not usernames:
            console.print("[yellow]No usernames provided.[/yellow]")
            return
        try:
            class_report = self._generate_class_report(usernames)
            self._display_class_report(class_report)
            self._export_class_report(class_report)
        except Exception as e:
            console.print(f"[red]Failed to generate class report: {e}[/red]")

    def _generate_class_report(self, usernames: List[str]):
        # Aggregate student reports
        total_students = len(usernames)
        total_mastered = 0
        total_correct = 0
        weak_concept_counter = {}
        for username in usernames:
            report = generate_student_report(username, self.content_manager)
            total_mastered += report["mastered_concepts"]
            total_correct += report["total_correct"]
            for wc in report["weak_concepts"]:
                key = (wc["subject"], wc["topic"], wc["concept"])
                weak_concept_counter[key] = weak_concept_counter.get(key, 0) + 1
        avg_mastered = total_mastered / total_students if total_students else 0
        avg_correct = total_correct / total_students if total_students else 0
        threshold = max(1, int(0.3 * total_students))
        class_weak_concepts = [
            {"subject": s, "topic": t, "concept": c, "count": count}
            for (s, t, c), count in weak_concept_counter.items() if count >= threshold
        ]
        return {
            "total_students": total_students,
            "average_mastered_concepts": avg_mastered,
            "average_total_correct": avg_correct,
            "class_weak_concepts": class_weak_concepts
        }

    def _display_class_report(self, class_report):
        table = Table(title="Class Report", show_lines=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total Students", str(class_report["total_students"]))
        table.add_row("Average Mastered Concepts", f"{class_report['average_mastered_concepts']:.2f}")
        table.add_row("Average Total Correct", f"{class_report['average_total_correct']:.2f}")
        table.add_row("Class Weak Concepts", str(len(class_report["class_weak_concepts"])))
        console.print(table)
        if class_report["class_weak_concepts"]:
            wc_table = Table(title="Class Weak Concepts (≥30% students)", show_lines=True)
            wc_table.add_column("Subject", style="cyan")
            wc_table.add_column("Topic", style="magenta")
            wc_table.add_column("Concept", style="yellow")
            wc_table.add_column("# Students", style="white")
            for wc in class_report["class_weak_concepts"]:
                wc_table.add_row(wc["subject"], wc["topic"], wc["concept"], str(wc["count"]))
            console.print(wc_table)

    def _export_class_report(self, class_report):
        if Confirm.ask("Export class report as CSV?"):
            filename = Prompt.ask("Enter CSV filename", default="class_report.csv")
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Total Students", class_report["total_students"]])
                writer.writerow(["Average Mastered Concepts", f"{class_report['average_mastered_concepts']:.2f}"])
                writer.writerow(["Average Total Correct", f"{class_report['average_total_correct']:.2f}"])
                writer.writerow([])
                writer.writerow(["Class Weak Concepts"])
                writer.writerow(["Subject", "Topic", "Concept", "# Students"])
                for wc in class_report["class_weak_concepts"]:
                    writer.writerow([wc["subject"], wc["topic"], wc["concept"], wc["count"]])
            console.print(f"[green]Class report exported to {filename}[/green]")
        if Confirm.ask("Export class report as JSON?"):
            filename = Prompt.ask("Enter JSON filename", default="class_report.json")
            with open(filename, 'w', encoding='utf-8') as f:
                import json
                json.dump(class_report, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Class report exported to {filename}[/green]")

if __name__ == "__main__":
    cli = TeacherAnalyticsCLI()
    cli.start() 