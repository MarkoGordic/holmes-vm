"""UI components for Holmes VM setup - Enhanced with Sherlock Holmes theme"""

from .colors import *
from .window import UI, is_tk_available

try:
    from .rich_console import RichConsoleUI, is_rich_available
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
