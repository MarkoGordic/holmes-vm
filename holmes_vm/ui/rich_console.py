#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rich Console UI for Holmes VM Setup
Beautiful terminal interface with animations and progress tracking
"""

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.align import Align
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Progress = None

from typing import Optional, List, Dict, Any
import time


# Sherlock Holmes themed banner
HOLMES_BANNER = r"""
   _____ _               _            _      _   _       _                 
  / ____| |             | |          | |    | | | |     | |                
 | (___ | |__   ___ _ __| | ___   ___| | __ | |_| | ___ | |_ __ ___   ___ 
  \___ \| '_ \ / _ \ '__| |/ _ \ / __| |/ / |  _  |/ _ \| | '_ ` _ \ / _ \
  ____) | | | |  __/ |  | | (_) | (__|   <  | | | | (_) | | | | | | |  __/
 |_____/|_| |_|\___|_|  |_|\___/ \___|_|\_\ \_| |_/\___/|_|_| |_| |_|\___|
                                                                            
            🔍 Digital Forensics VM Setup • Elementary, my dear Watson
"""


class RichConsoleUI:
    """Enhanced console UI using Rich library"""
    
    def __init__(self, title: str = "Holmes VM Setup"):
        if not RICH_AVAILABLE:
            raise RuntimeError("Rich library not available")
        
        self.console = Console()
        self.title = title
        self.current_step = 0
        self.total_steps = 0
        self.current_step_name = ""
        self.start_time = time.time()
        self.step_start_time = time.time()
        
    def show_banner(self):
        """Display the Holmes VM banner"""
        banner_text = Text(HOLMES_BANNER, style="bold #A0826D")  # Victorian brown
        self.console.print(Align.center(banner_text))
        self.console.print()
    
    def show_welcome(self, message: str = "Preparing to set up your digital forensics environment..."):
        """Show welcome message in a panel"""
        welcome_panel = Panel(
            message,
            title="[bold #A0826D]Welcome Detective[/bold #A0826D]",
            border_style="#A0826D",  # Victorian brown
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(welcome_panel)
        self.console.print()
    
    def create_progress(self) -> Progress:
        """Create a styled progress bar"""
        return Progress(
            SpinnerColumn(spinner_name="dots", style="#A0826D"),  # Victorian brown
            TextColumn("[bold #9A9593]{task.description}", justify="left"),  # Warm gray
            BarColumn(bar_width=50, style="#A0826D", complete_style="#7A9A6F"),  # Brown/muted green
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            expand=False
        )
    
    def show_selection_prompt(self):
        """Show component selection prompt"""
        prompt_panel = Panel(
            "[#C9A56D]Starting interactive selection mode...[/#C9A56D]\n"  # Golden brown
            "The GUI will open to let you choose components to install.",
            title="[bold]Component Selection[/bold]",
            border_style="#C9A56D",  # Golden brown
            padding=(1, 2)
        )
        self.console.print(prompt_panel)
    
    def start_step(self, step_num: int, total: int, step_name: str):
        """Start a new installation step"""
        self.current_step = step_num
        self.total_steps = total
        self.current_step_name = step_name
        self.step_start_time = time.time()
        
        step_header = Text()
        step_header.append(f"[{step_num}/{total}] ", style="bold #A0826D")  # Victorian brown
        step_header.append(step_name, style="bold white")
        step_header.append(" 🔍", style="#C9A56D")  # Golden brown
        
        self.console.print()
        self.console.rule(step_header, style="#A0826D")  # Victorian brown
    
    def log_info(self, message: str, prefix: str = "→"):
        """Log an info message"""
        self.console.print(f"  [#9A9593]{prefix}[/#9A9593] {message}")  # Warm gray
    
    def log_success(self, message: str):
        """Log a success message"""
        self.console.print(f"  [#7A9A6F]✓[/#7A9A6F] {message}", style="#7A9A6F")  # Muted green
    
    def log_warning(self, message: str):
        """Log a warning message"""
        self.console.print(f"  [#C9A56D]⚠[/#C9A56D] {message}", style="#C9A56D")  # Golden brown
    
    def log_error(self, message: str):
        """Log an error message"""
        self.console.print(f"  [#B86A60]✗[/#B86A60] {message}", style="#B86A60")  # Muted red
    
    def log_verbose(self, message: str):
        """Log a verbose/debug message (dimmed)"""
        self.console.print(f"    [dim]{message}[/dim]")
    
    def complete_step(self, success: bool = True):
        """Mark current step as complete"""
        elapsed = time.time() - self.step_start_time
        status = "[#7A9A6F]COMPLETE[/#7A9A6F]" if success else "[#B86A60]FAILED[/#B86A60]"
        self.console.print(f"  {status} [dim]({elapsed:.1f}s)[/dim]")
    
    def show_summary(self, stats: Dict[str, Any]):
        """Show installation summary"""
        elapsed = time.time() - self.start_time
        mm, ss = divmod(int(elapsed), 60)
        hh, mm = divmod(mm, 60)
        
        summary_table = Table(
            title="[bold #A0826D]Investigation Summary[/bold #A0826D]",  # Victorian brown
            box=box.DOUBLE_EDGE,
            border_style="#A0826D",  # Victorian brown
            show_header=False,
            padding=(0, 2)
        )
        
        summary_table.add_column("Metric", style="bold white")
        summary_table.add_column("Value", style="#A0826D")  # Victorian brown
        
        summary_table.add_row("Total Time", f"{hh:02d}:{mm:02d}:{ss:02d}")
        summary_table.add_row("Steps Completed", f"{stats.get('completed', 0)}/{stats.get('total', 0)}")
        
        if stats.get('errors', 0) > 0:
            summary_table.add_row("Errors", f"[#B86A60]{stats.get('errors', 0)}[/#B86A60]")  # Muted red
        if stats.get('warnings', 0) > 0:
            summary_table.add_row("Warnings", f"[#C9A56D]{stats.get('warnings', 0)}[/#C9A56D]")  # Golden brown
        
        self.console.print()
        self.console.print(summary_table)
        self.console.print()
    
    def show_completion(self, success: bool = True):
        """Show completion message"""
        if success:
            completion_panel = Panel(
                "[bold #7A9A6F]✓ Holmes VM setup completed successfully![/bold #7A9A6F]\n\n"  # Muted green
                "[white]Your digital forensics environment is ready.[/white]\n"
                "[dim]The game is afoot! 🔍[/dim]",
                title="[bold #7A9A6F]Investigation Ready[/bold #7A9A6F]",  # Muted green
                border_style="#7A9A6F",  # Muted green
                box=box.DOUBLE,
                padding=(1, 2)
            )
        else:
            completion_panel = Panel(
                "[bold #B86A60]Setup encountered issues.[/bold #B86A60]\n\n"  # Muted red
                "[white]Please check the logs for details.[/white]\n"
                "[dim]The investigation continues... 🔍[/dim]",
                title="[bold #C9A56D]Attention Required[/bold #C9A56D]",  # Golden brown
                border_style="#C9A56D",  # Golden brown
                box=box.DOUBLE,
                padding=(1, 2)
            )
        
        self.console.print(completion_panel)
    
    def show_error_panel(self, error_msg: str, details: Optional[str] = None):
        """Show error in a panel"""
        content = f"[bold #B86A60]{error_msg}[/bold #B86A60]"  # Muted red
        if details:
            content += f"\n\n[dim]{details}[/dim]"
        
        error_panel = Panel(
            content,
            title="[bold #B86A60]Error[/bold #B86A60]",  # Muted red
            border_style="#B86A60",  # Muted red
            box=box.HEAVY,
            padding=(1, 2)
        )
        self.console.print(error_panel)
    
    def prompt_continue(self, message: str = "Press Enter to continue...") -> bool:
        """Prompt user to continue"""
        try:
            self.console.print(f"\n[dim]{message}[/dim]", end="")
            input()
            return True
        except KeyboardInterrupt:
            return False


class RichProgressTracker:
    """Wrapper for Rich progress tracking with context manager support"""
    
    def __init__(self, console_ui: RichConsoleUI, description: str):
        self.console_ui = console_ui
        self.description = description
        self.progress = console_ui.create_progress()
        self.task_id = None
    
    def __enter__(self):
        self.progress.__enter__()
        self.task_id = self.progress.add_task(self.description, total=100)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.__exit__(exc_type, exc_val, exc_tb)
    
    def update(self, completed: float, description: Optional[str] = None):
        """Update progress"""
        if self.task_id is not None:
            if description:
                self.progress.update(self.task_id, completed=completed, description=description)
            else:
                self.progress.update(self.task_id, completed=completed)
    
    def advance(self, amount: float):
        """Advance progress by amount"""
        if self.task_id is not None:
            self.progress.advance(self.task_id, amount)


def is_rich_available() -> bool:
    """Check if Rich library is available"""
    return RICH_AVAILABLE
