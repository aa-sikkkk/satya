# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
CLI Renderer Module

This module handles the visual presentation for the CLI using the Rich library.
It separates the 'View' logic from the 'Controller' logic in cli_interface.py.
"""

from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text

# Configure rich console
console = Console()

class CLIRenderer:
    """Handles all visual output for the CLI."""
    
    @staticmethod
    def show_welcome_message():
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
2. ❓ Ask Questions - Get AI-powered answers with RAG-enhanced content discovery
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

    @staticmethod
    def show_help(context: str = "main"):
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
- Get AI-powered answers with RAG-enhanced content discovery
- Answers use both structured content and intelligent content retrieval
- Get confidence scores and source information
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

    @staticmethod
    def show_model_info(model_info: Dict[str, Any]):
        """Display information about the current AI model."""
        if not model_info:
            console.print(Panel(
                "[yellow]Could not retrieve model information.[/yellow]",
                title="Model Warning",
                border_style="yellow"
            ))
            return

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

    @staticmethod
    def display_concept(concept: Dict[str, Any]):
        """Display a concept and its content."""
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

    @staticmethod
    def render_menu(title: str, options: List[str]):
        """Render a menu table (does not handle input)."""
        table = Table(title=title, show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="green")
        
        for i, option in enumerate(options, 1):
            table.add_row(str(i), option)
            
        console.print(table)
        console.print("\nPress 'h' for help, 'q' to exit")

    @staticmethod
    def show_progress_summary(total_questions, total_correct, accuracy, len_mastered):
        """Display the main progress summary card."""
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
            f"🏆 Concepts Mastered: {len_mastered}",
            title="Your Learning Journey",
            border_style="cyan"
        ))

    @staticmethod
    def show_subject_progress(subject_stats: Dict):
        """Display progress bars for each subject."""
        console.print("\n📚 Your Progress in Each Subject:")
        for subject, stats in subject_stats.items():
            progress_pct = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            progress_bar = "■" * int(progress_pct / 10) + "□" * (10 - int(progress_pct / 10))
            
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

    @staticmethod
    def show_weak_topics(weak_list: List[Tuple]):
        """Display weak topics."""
        if weak_list:
            console.print("\n📌 Topics to Review:")
            for s, t, c, q in weak_list:
                console.print(Panel(
                    f"Subject: {s}\n"
                    f"Topic: {t}\n"
                    f"Concept: {c}\n"
                    f"Question: {q}",
                    border_style="yellow"
                ))

    @staticmethod
    def show_next_concept_suggestion(suggestion: Tuple[str, str, str]):
        """Display next concept suggestion."""
        if suggestion:
            s, t, c = suggestion
            console.print(Panel(
                f"Ready for your next challenge? 🎯\n\n"
                f"Try learning about: {c}\n"
                f"in {t} ({s})",
                title="Keep Learning!",
                border_style="green"
            ))

    # =========================================================================
    # DIAGRAM RENDERING (Rich Library Integration)
    # =========================================================================
    
    # Concept-aware styling for different diagram types
    DIAGRAM_STYLES = {
        'process': {'color': 'orange3', 'icon': '📊', 'title': 'Process Flow'},
        'flowchart': {'color': 'orange3', 'icon': '📊', 'title': 'Flowchart'},
        'comparison': {'color': 'cyan', 'icon': '⚖️', 'title': 'Comparison Table'},
        'hierarchy': {'color': 'green', 'icon': '🌳', 'title': 'Structure Diagram'},
        'structure': {'color': 'green', 'icon': '🌳', 'title': 'Structure Diagram'},
        'cycle': {'color': 'magenta', 'icon': '🔄', 'title': 'Cycle Diagram'},
        'default': {'color': 'white', 'icon': '📈', 'title': 'Visual Representation'}
    }
    
    @staticmethod
    def render_diagram(diagram_content: str, diagram_type: str = 'default', source: str = None):
        """
        Render a diagram with rich styling based on concept type.
        
        Args:
            diagram_content: The ASCII diagram text
            diagram_type: One of 'process', 'comparison', 'hierarchy', 'cycle'
            source: Optional source info (e.g., 'Generated', 'Knowledge Base')
        """
        # Normalize diagram type
        dtype = diagram_type.lower() if diagram_type else 'default'
        if hasattr(diagram_type, 'value'):  # Handle enum
            dtype = diagram_type.value.lower()
        
        style = CLIRenderer.DIAGRAM_STYLES.get(dtype, CLIRenderer.DIAGRAM_STYLES['default'])
        
        # Build title
        title = f"{style['icon']} {style['title']}"
        if source:
            title += f" - {source}"
        
        # Render with rich Panel
        console.print(Panel(
            diagram_content,
            title=title,
            border_style=style['color'],
            expand=False
        ))
    
    @staticmethod
    def render_comparison_table(similarities: List[str], differences: List[str], 
                                 item_a: str = "Item A", item_b: str = "Item B"):
        """
        Render a comparison as a rich Table instead of ASCII art.
        
        This provides much cleaner terminal output than ASCII table characters.
        
        Args:
            similarities: List of similarity points
            differences: List of difference points  
            item_a: Name of first item being compared
            item_b: Name of second item being compared
        """
        # Similarities section
        if similarities:
            sim_table = Table(title="✓ Similarities", border_style="cyan")
            sim_table.add_column("Both share these characteristics", style="cyan")
            for sim in similarities:
                sim_table.add_row(f"• {sim}")
            console.print(sim_table)
        
        # Differences section
        if differences:
            diff_table = Table(title="⚡ Differences", border_style="yellow")
            diff_table.add_column(item_a, style="green")
            diff_table.add_column(item_b, style="magenta")
            
            # Parse differences if they contain vs. pattern
            for diff in differences:
                if ' vs ' in diff.lower() or ' vs. ' in diff.lower():
                    parts = diff.replace(' vs. ', ' vs ').split(' vs ', 1)
                    if len(parts) == 2:
                        diff_table.add_row(parts[0].strip(), parts[1].strip())
                    else:
                        diff_table.add_row(diff, "-")
                else:
                    diff_table.add_row(diff, "-")
            
            console.print(diff_table)
    
    @staticmethod
    def render_process_steps(steps: List[str]):
        """
        Render process steps as a rich Table with numbered steps.
        
        Cleaner than ASCII flowcharts for terminal display.
        """
        table = Table(title="📊 Process Steps", border_style="orange3")
        table.add_column("#", style="bold orange3", width=3)
        table.add_column("Step", style="white")
        
        for i, step in enumerate(steps, 1):
            table.add_row(str(i), step.strip())
        
        console.print(table)

