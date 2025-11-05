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

# Import theme colors (teal-blue palette)
from holmes_vm.ui.colors import (
    COLOR_ACCENT,
    COLOR_ACCENT_LIGHT,
    COLOR_ACCENT_DARK,
    COLOR_MUTED,
    COLOR_SUCCESS,
    COLOR_WARN,
    COLOR_ERROR,
    COLOR_FG_BRIGHT,
    COLOR_BG,
)


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
        banner_text = Text(HOLMES_BANNER, style=f"bold {COLOR_ACCENT}")
        self.console.print(Align.center(banner_text))
        self.console.print()
    
    def show_welcome(self, message: str = "Preparing to set up your digital forensics environment..."):
        """Show welcome message in a panel"""
        welcome_panel = Panel(
            message,
            title=f"[bold {COLOR_ACCENT}]Welcome Detective[/bold {COLOR_ACCENT}]",
            border_style=COLOR_ACCENT,
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(welcome_panel)
        self.console.print()
    
    def create_progress(self) -> Any:
        """Create a styled progress bar"""
        return Progress(
            SpinnerColumn(spinner_name="dots", style=COLOR_ACCENT),
            TextColumn(f"[bold {COLOR_MUTED}]{{task.description}}", justify="left"),
            BarColumn(bar_width=50, style=COLOR_ACCENT, complete_style=COLOR_SUCCESS),
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
            f"[{COLOR_WARN}]Starting interactive selection mode...[/]\n"
            "The GUI will open to let you choose components to install.",
            title="[bold]Component Selection[/bold]",
            border_style=COLOR_WARN,
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
        step_header.append(f"[{step_num}/{total}] ", style=f"bold {COLOR_ACCENT}")
        step_header.append(step_name, style=f"bold {COLOR_FG_BRIGHT}")
        step_header.append(" 🔍", style=COLOR_ACCENT_LIGHT)
        
        self.console.print()
        self.console.rule(step_header, style=COLOR_ACCENT)
    
    def log_info(self, message: str, prefix: str = "→"):
        """Log an info message"""
        self.console.print(f"  [{COLOR_MUTED}]{prefix}[/] {message}")
    
    def log_success(self, message: str):
        """Log a success message"""
        self.console.print(f"  [{COLOR_SUCCESS}]✓[/] {message}", style=COLOR_SUCCESS)
    
    def log_warning(self, message: str):
        """Log a warning message"""
        self.console.print(f"  [{COLOR_WARN}]⚠[/] {message}", style=COLOR_WARN)
    
    def log_error(self, message: str):
        """Log an error message"""
        self.console.print(f"  [{COLOR_ERROR}]✗[/] {message}", style=COLOR_ERROR)
    
    def log_verbose(self, message: str):
        """Log a verbose/debug message (dimmed)"""
        self.console.print(f"    [dim]{message}[/dim]")
    
    def complete_step(self, success: bool = True):
        """Mark current step as complete"""
        elapsed = time.time() - self.step_start_time
        status = f"[{COLOR_SUCCESS}]COMPLETE[/]" if success else f"[{COLOR_ERROR}]FAILED[/]"
        self.console.print(f"  {status} [dim]({elapsed:.1f}s)[/dim]")
    
    def show_summary(self, stats: Dict[str, Any]):
        """Show installation summary"""
        elapsed = time.time() - self.start_time
        mm, ss = divmod(int(elapsed), 60)
        hh, mm = divmod(mm, 60)
        
        summary_table = Table(
            title=f"[bold {COLOR_ACCENT}]Investigation Summary[/bold {COLOR_ACCENT}]",
            box=box.DOUBLE_EDGE,
            border_style=COLOR_ACCENT,
            show_header=False,
            padding=(0, 2)
        )
        
        summary_table.add_column("Metric", style=f"bold {COLOR_FG_BRIGHT}")
        summary_table.add_column("Value", style=COLOR_ACCENT)
        
        summary_table.add_row("Total Time", f"{hh:02d}:{mm:02d}:{ss:02d}")
        summary_table.add_row("Steps Completed", f"{stats.get('completed', 0)}/{stats.get('total', 0)}")
        
        if stats.get('errors', 0) > 0:
            summary_table.add_row("Errors", f"[{COLOR_ERROR}]{stats.get('errors', 0)}[/]")
        if stats.get('warnings', 0) > 0:
            summary_table.add_row("Warnings", f"[{COLOR_WARN}]{stats.get('warnings', 0)}[/]")
        
        self.console.print()
        self.console.print(summary_table)
        self.console.print()
    
    def show_completion(self, success: bool = True):
        """Show completion message"""
        if success:
            completion_panel = Panel(
                f"[bold {COLOR_SUCCESS}]✓ Holmes VM setup completed successfully![/bold {COLOR_SUCCESS}]\n\n"
                "[white]Your digital forensics environment is ready.[/white]",
                title=f"[bold {COLOR_SUCCESS}]Investigation Ready[/bold {COLOR_SUCCESS}]",
                border_style=COLOR_SUCCESS,
                box=box.DOUBLE,
                padding=(1, 2)
            )
        else:
            completion_panel = Panel(
                f"[bold {COLOR_ERROR}]Setup encountered issues.[/bold {COLOR_ERROR}]\n\n"
                "[white]Please check the logs for details.[/white]",
                title=f"[bold {COLOR_WARN}]Attention Required[/bold {COLOR_WARN}]",
                border_style=COLOR_WARN,
                box=box.DOUBLE,
                padding=(1, 2)
            )
        
        self.console.print(completion_panel)
    
    def show_error_panel(self, error_msg: str, details: Optional[str] = None):
        """Show error in a panel"""
        content = f"[bold {COLOR_ERROR}]{error_msg}[/bold {COLOR_ERROR}]"
        if details:
            content += f"\n\n[dim]{details}[/dim]"
        
        error_panel = Panel(
            content,
            title=f"[bold {COLOR_ERROR}]Error[/bold {COLOR_ERROR}]",
            border_style=COLOR_ERROR,
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
    
    def __init__(self, console_ui: 'RichConsoleUI', description: str):
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
