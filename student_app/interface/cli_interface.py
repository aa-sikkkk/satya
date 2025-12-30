"""
CLI Interface Module

This module provides the command-line interface for students to interact with
the NEBedu learning system.
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
from system.rag.rag_retrieval_engine import RAGRetrievalEngine

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
        
        # Initialize RAG retrieval engine
        try:
            self.rag_engine = RAGRetrievalEngine()

        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {str(e)}")
            console.print(Panel(
                "[yellow]Warning: RAG engine not available. Using basic content search.[/yellow]",
                title="RAG Warning",
                border_style="yellow"
            ))
            self.rag_engine = None
        
        # Ensure model path exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")
            
        # Initialize model handler with proper path
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
    
    def _create_menu_with_index(self, title: str, options: List[str]) -> Any:
        """
        Create and display a menu and return both index (1-based) and label.
        
        Returns:
            (int, str): Tuple of (selected_index_1_based, selected_label)
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
        
        # Data-driven grading: rubric-based scoring derived from content
        from difflib import SequenceMatcher
        import re
        STOPWORDS = set([
            "the","is","are","a","an","to","of","and","or","for","in","on","at","by","that",
            "this","it","as","be","with","from","into","their","its","they","them","can","will",
            "about","how","what","why","which","who","whose","when","where","than","then","also"
        ])
        def _stem(token: str) -> str:
            # very light stemming to improve overlap
            for suf in ("ing","ed","es","s"):
                if token.endswith(suf) and len(token) - len(suf) >= 3:
                    return token[: -len(suf)]
            return token
        def tokenize(text: str):
            tokens = re.findall(r"[a-zA-Z]+", text.lower())
            return [_stem(t) for t in tokens if len(t) >= 3 and t not in STOPWORDS]
        def build_rubric(ref_texts):
            # Build frequency-based keyword rubric from acceptable answers
            freq = {}
            for rt in ref_texts:
                for t in set(tokenize(rt)):
                    freq[t] = freq.get(t, 0) + 1
            # Keep top keywords that appear across references
            common = [t for t, c in freq.items() if c >= max(1, len(ref_texts)//2)]
            # Ensure at least some keywords
            if not common:
                # fallback to top 8 tokens by frequency
                common = [t for t, _ in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:8]]
            return set(common)
        # Prefer explicit rubric if present in question
        explicit_rubric = set(question.get('rubric_keywords', []))
        acc = [a for a in question.get('acceptable_answers', []) if isinstance(a, str)]
        # Save acceptable answers for later steps
        try:
            self._last_acceptable_answers = acc if acc else None
        except Exception:
            self._last_acceptable_answers = None
        rubric = explicit_rubric if explicit_rubric else build_rubric(acc) if acc else set()
        user_tokens = set(tokenize(answer))
        # Similarity components
        keyword_overlap = len(user_tokens & rubric) / max(1, len(rubric)) if rubric else 0.0
        fuzzy_max = max((SequenceMatcher(None, answer.lower(), rt.lower()).ratio() for rt in acc), default=0.0)
        # Weighted score (favor keyword coverage to reduce verbosity dependency)
        score = 0.8 * keyword_overlap + 0.2 * fuzzy_max
        # Decide correctness based on thresholds; require minimum coverage to avoid false positives
        threshold = float(question.get('rubric_threshold', 0.45))
        min_coverage = float(question.get('rubric_min_coverage', 0.50))
        correct = (score >= threshold) and (keyword_overlap >= min_coverage)

        # Optional fast model-based judge for borderline/false negatives
        margin_low = threshold - 0.12
        margin_high = threshold + 0.05
        if not correct and acc and (score >= margin_low and score < margin_high):
            try:
                # Reuse the existing quick inference helper via a minimal inline definition
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
                def _quick_answer(prompt_text: str, context_text: str, length: str, timeout_seconds: int = 1):
                    try:
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            fut = executor.submit(self.model_handler.get_answer, prompt_text, context_text, length)
                            return fut.result(timeout=timeout_seconds)
                    except FuturesTimeoutError:
                        return (None, 0.0)
                    except Exception:
                        return (None, 0.0)
                # Compact grading context using rubric keywords to minimize prompt size
                rubric_preview = ", ".join(list(rubric)[:8]) if rubric else ""
                grading_context = (
                    f"Question: {question.get('question','')[:140]}\n"
                    f"Key points to check: {rubric_preview}\n"
                    f"Student answer: {answer[:220]}\n"
                    "Reply 'Yes' if the answer correctly covers the key points, otherwise 'No'."
                )
                judge_reply, _ = _quick_answer("Is the answer correct?", grading_context, "very_short", timeout_seconds=1)
                if isinstance(judge_reply, str) and judge_reply.strip().lower().startswith("yes"):
                    correct = True
            except Exception:
                pass
        # Optional fast model-based veto for borderline/false positives
        if correct and acc and (score < (threshold + 0.10)):
            try:
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
                def _quick_judge(prompt_text: str, context_text: str, timeout_seconds: float = 1.2):
                    try:
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            fut = executor.submit(self.model_handler.get_answer, prompt_text, context_text, "very_short")
                            res = fut.result(timeout=timeout_seconds)
                            return res[0] if isinstance(res, tuple) else res
                    except (FuturesTimeoutError, Exception):
                        return None
                q_text = question.get('question','') or (self._last_question_text or '')
                ctx = acc[0][:240]
                judge_prompt = (
                    f"{q_text}\n\nStudent answer: {answer[:240]}\n\nUsing ONLY the context, is the student correct? Reply 'Yes' or 'No'."
                )
                reply = _quick_judge(judge_prompt, ctx, timeout_seconds=1.2)
                if isinstance(reply, str) and reply.strip().lower().startswith('no'):
                    correct = False
            except Exception:
                pass
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
        if want_expl:
            # Prefer per-question explanation if present
            explanation = question.get('explanation')
            # Ultra-fast model-based explanation with tiny context and ~0.8s timeout
            if not explanation:
                try:
                    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
                    def _quick_explain(prompt_text: str, context_text: str, timeout_seconds: float = 0.8):
                        try:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                fut = executor.submit(self.model_handler.get_answer, prompt_text, context_text, "very_short")
                                res = fut.result(timeout=timeout_seconds)
                                return res[0] if isinstance(res, tuple) else res
                        except (FuturesTimeoutError, Exception):
                            return None
                    # Build a compact, question-specific context (prefer acceptable_answers)
                    q_text = question.get('question', '') or (self._last_question_text or '')
                    base_context = None
                    if acc and len(acc) > 0:
                        base_context = acc[0][:240]
                    # Only fall back to concept summary if no acceptable answer exists
                    if (not base_context or len(base_context.strip()) == 0):
                        cs = concept_summary or self._last_concept_summary
                        if cs:
                            # Fast: use first 240 chars instead of sentence matching
                            base_context = cs[:240]
                    base_context = (base_context or "").strip()[:240]
                    # Ask with the actual question to keep it on-topic
                    ask_text = (
                        f"{q_text} \n\nInstruction: Using ONLY the context, answer in exactly 2 short, simple sentences for Grade 10. Stay on-topic."
                    )
                    explanation = _quick_explain(ask_text, base_context, timeout_seconds=1.2)
                except Exception:
                    explanation = None
            if not explanation:
                # Instant fallback: 1-2 sentences from concept summary, else rubric
                # Prefer compressing the current question's acceptable answer first
                if acc:
                    # Take first acceptable answer and compress to 1-2 sentences
                    a0 = acc[0]
                    # Split by sentence delimiters; join first 2
                    parts = [p.strip() for p in re.split(r"[\.!?]", a0) if p.strip()]
                    explanation = '. '.join(parts[:2]) + ('.' if parts[:2] else '')
                # If not available, use 1-2 sentences from the concept summary
                if (not explanation or len(explanation.strip()) == 0) and concept_summary:
                    sentences = [s.strip() for s in concept_summary.split('.') if s.strip()]
                    explanation = '. '.join(sentences[:2]) + ('.' if sentences[:2] else '')
                if (not explanation) or (len(explanation.strip()) == 0):
                    rubric_preview = ", ".join(list(rubric)[:6]) if 'rubric' in locals() and rubric else ""
                    explanation = f"In simple terms: {rubric_preview}." if rubric_preview else 'No explanation available.'
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
            
    def _stream_answer(self, question: str, context: str, answer_length: str, source_info: str = "") -> Tuple[str, float]:
        """
        Stream answer tokens and display them in real-time.
        
        Returns:
            Tuple[str, float]: Complete answer and confidence score
        """
        accumulated_answer = ""
        confidence = 0.8  # Default confidence, will be calculated after
        
        def create_panel():
            """Create a panel with current accumulated answer."""
            content = f"[bold]{accumulated_answer}[/bold]"
            if source_info:
                content += f"\n\n[cyan]Source: {source_info}[/cyan]"
            return Panel(
                content,
                title="Answer",
                border_style="green"
            )
        
        try:
            # Start streaming with live display
            with Live(create_panel(), refresh_per_second=10, console=console) as live:
                for token in self.model_handler.get_answer_stream(question, context, answer_length):
                    accumulated_answer += token
                    # Update the panel with new content
                    live.update(create_panel())
            
            # After streaming completes, generate and append diagram (non-blocking)
            try:
                from system.diagrams import generate_and_append_diagram
                accumulated_answer = generate_and_append_diagram(question, accumulated_answer)
                # Update display with diagram if added
                live.update(create_panel())
            except Exception as e:
                # Graceful fallback: continue with original answer if diagram generation fails
                logger.debug(f"Diagram generation failed: {e}")
            
            # Calculate confidence after streaming completes
            if accumulated_answer and len(accumulated_answer.strip()) >= 10:
                # Use a quick confidence calculation
                confidence = self._calculate_quick_confidence(accumulated_answer, context)
            else:
                confidence = 0.1
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            accumulated_answer = "I'm having trouble processing your question. Please try again."
            confidence = 0.1
        
        return accumulated_answer.strip(), confidence
    
    def _calculate_quick_confidence(self, answer: str, context: str) -> float:
        """
        Quick confidence calculation for streaming answers.
        Focuses on answer quality and completeness, not just word count.
        """
        answer_lower = answer.lower()
        
        # Error detection
        if any(phrase in answer_lower for phrase in ["i couldn't", "i'm having trouble", "error"]):
            return 0.1
        
        word_count = len(answer.split())
        if word_count < 5:
            return 0.3
        
        # Check if RAG context was provided
        has_rag_context = context and len(context.strip()) > 50
        
        # Quality indicators
        has_structure = answer.count(".") >= 2
        has_definition = any(phrase in answer_lower for phrase in ["is a", "is an", "are", "means", "refers to"])
        has_examples = any(word in answer_lower for word in ["example", "like", "such as"])
        is_complete = word_count >= 15 and has_structure
        
        # Base confidence - high for complete, quality answers
        if is_complete:
            base_score = 0.85  # High confidence for complete answers
        elif has_structure:
            base_score = 0.75  # Good confidence for structured answers
        else:
            base_score = 0.65  # Lower for incomplete answers
        
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
            
        return min(1.0, base_score)
    
    @timeit
    def _handle_free_text_question(self, question: str) -> None:
        """Handle free-text questions using the AI model with streaming."""
        def _quick_answer(prompt: str, context: str, length: str, timeout_seconds: int = 30):
            """Call model with a timeout; on failure/timeout return (None, 0.0)."""
            try:
                if timeout_seconds is None or timeout_seconds <= 0:
                    # Direct, no-timeout call
                    return self.model_handler.get_answer(prompt, context, length)
                with ThreadPoolExecutor(max_workers=1) as executor:
                    fut = executor.submit(self.model_handler.get_answer, prompt, context, length)
                    return fut.result(timeout=timeout_seconds)
            except FuturesTimeoutError:
                logger.warning("Model inference timed out; falling back to fast path.")
                return None, 0.0
            except Exception as e:
                logger.error(f"Model inference error: {str(e)}")
                return None, 0.0
        
        try:
            # Show normalized question if it was changed
            original_question = question
            normalized_question = question.strip()
            if normalized_question.isupper():
                normalized_question = normalized_question.lower().capitalize()
                if normalized_question != original_question:
                    console.print(f"[yellow]Note: I'll answer: '{normalized_question}'[/yellow]")
            elif normalized_question.islower():
                normalized_question = normalized_question.capitalize()
                if normalized_question != original_question:
                    console.print(f"[yellow]Note: I'll answer: '{normalized_question}'[/yellow]")
            
            # Always use medium for detailed answers (optimized for speed)
            answer_length = "medium"
            
            # Ensure model is loaded
            if not self.model_handler.phi15_handler.llm:
                self.model_handler.phi15_handler.load_model()
                
            with console.status("[bold green]Generating detailed answer...[/bold green]"):
                log_resource_usage("Before model inference")
                
                # Use optimized non-blocking RAG helper (fast, with timeout)
                from system.rag.rag_helper import get_context_non_blocking
                
                try:
                    context, source_info = get_context_non_blocking(
                        self.rag_engine,
                        question,
                        content_manager=self.content_manager,
                        timeout_seconds=0.5  # 0.5 second timeout - fast fallback to structured content
                    )
                    
                    # Get relevant content for display (non-blocking, quick)
                    relevant_content = None
                    if source_info == "Structured content":
                        try:
                            relevant_content = self.content_manager.search_content(question)
                        except Exception:
                            pass
                    
                    # Generate answer with streaming (context is already ready, no blocking)
                    try:
                        answer, confidence = self._stream_answer(question, context, answer_length, source_info)
                        if not answer or len(answer.strip()) == 0:
                            raise ValueError("Model generated empty answer")
                    except Exception as e:
                        logger.error(f"Model inference error: {str(e)}")
                        # Final fallback
                        general_context = (
                            "You are a helpful AI tutor for Grade 8-12 students in Nepal. "
                            "Use your knowledge of Grade 8-12 curriculum (NEB standards) to provide an accurate answer."
                        )
                        try:
                            answer, confidence = self._stream_answer(question, general_context, answer_length, "AI General Knowledge (Fallback)")
                            source_info = "AI General Knowledge (Fallback)"
                        except Exception as e2:
                            logger.error(f"Fallback also failed: {str(e2)}")
                            answer = "I'm having trouble processing your question. Please try rephrasing it."
                            confidence = 0.1
                            source_info = "Error"
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
                
            # Display final answer with confidence indicator and source info
            # (Answer was already displayed during streaming, now show final stats)
            confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
            
            # Add source information if available
            source_display = ""
            if 'source_info' in locals():
                source_display = f"\n[cyan]Source: {source_info}[/cyan]"
            
            # Print final panel with confidence
            console.print(Panel(
                f"[{confidence_color}]Confidence: {confidence:.1%}[/{confidence_color}]"
                f"{source_display}",
                title="Answer Statistics",
                border_style="cyan"
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

            # Generate hints quickly (optimized for speed)
            try:
                # Use better context for relevant hints (use the same context as answer)
                hint_context = context if context else (relevant_content[0]['summary'] if relevant_content else context)
                # Generate hints in background for better UX
                hints = self.model_handler.get_hints(question, hint_context)
                if hints:
                    console.print("\n💡 Here are some hints to help you understand better:")
                    for hint in hints:
                        console.print(f"• {hint}")
            except Exception as e:
                logger.debug(f"Hints generation skipped: {e}")
                # Don't show error - hints are optional
            
            # Show related concepts - only if they're from the same subject
            if len(relevant_content) > 1:
                # Filter to same subject for relevance
                first_subject = relevant_content[0].get('subject', '')
                related = [item for item in relevant_content[1:4] 
                          if item.get('subject', '') == first_subject]
                if related:
                    console.print("\n📚 Related concepts you might want to study:")
                    for item in related[:2]:  # Show up to 2 related concepts from same subject
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
            # Keep model in memory for faster subsequent answers; cleanup handled on app exit.
            pass
            
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
        """Browse subjects and their content."""
        # Get subjects
        subjects = self.content_manager.get_all_subjects()
        if not subjects:
            console.print("[yellow]No subjects available.[/yellow]")
            return
            
        # Select subject
        subject = self._create_menu("Select a Subject", subjects)
        
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
                        topic=topic_name,
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
        model_path = os.path.join(base_dir, "satya_data", "models", "phi_1_5")
        
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