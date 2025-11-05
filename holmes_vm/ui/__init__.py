"""UI components for Holmes VM setup"""

from holmes_vm.ui.window import UI, is_tk_available

try:
    from holmes_vm.ui.rich_console import RichConsoleUI, is_rich_available
    RICH_AVAILABLE = is_rich_available()
except ImportError:
    RICH_AVAILABLE = False
    RichConsoleUI = None

__all__ = [
    'UI',
    'is_tk_available',
    'RichConsoleUI',
    'is_rich_available',
    'RICH_AVAILABLE',
]
