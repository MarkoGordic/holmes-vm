#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holmes VM Setup - Main entry point
Modular, extensible forensics VM setup tool with enhanced UI
"""

import sys
import argparse
import threading

from holmes_vm.core.config import get_config
from holmes_vm.core.logger import create_logger, get_default_log_dir
from holmes_vm.core.orchestrator import SetupOrchestrator

# Try to import Modern CustomTkinter UI first
try:
    from holmes_vm.ui.modern_window import ModernUI, is_ctk_available
    CTK_SUPPORT = is_ctk_available()
except ImportError:
    CTK_SUPPORT = False
    ModernUI = None

# Fallback to original tkinter UI
try:
    from holmes_vm.ui.window import UI, is_tk_available
    TK_SUPPORT = is_tk_available()
except ImportError:
    TK_SUPPORT = False
    UI = None

# Try to import Rich console
try:
    from holmes_vm.ui.rich_console import RichConsoleUI, is_rich_available
    RICH_SUPPORT = is_rich_available()
except ImportError:
    RICH_SUPPORT = False
    RichConsoleUI = None


APP_NAME = "Holmes VM Setup"


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Holmes VM Setup - Modular forensics VM installer'
    )
    parser.add_argument('--no-gui', action='store_true', help='Run in console mode without GUI')
    parser.add_argument('--what-if', action='store_true', help='Simulate installation without making changes')
    parser.add_argument('--force-reinstall', action='store_true', help='Force reinstallation of packages')
    parser.add_argument('--log-dir', default=get_default_log_dir(), help='Directory for log files')
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Initialize configuration
    config = get_config()
    
    # Determine which UI to use (prefer modern CustomTkinter > tkinter > Rich > plain)
    use_modern_gui = (not args.no_gui) and CTK_SUPPORT
    use_gui = (not args.no_gui) and TK_SUPPORT and not use_modern_gui
    
    ui = None
    rich_ui = None
    
    # Try modern CustomTkinter UI first
    if use_modern_gui:
        try:
            ui = ModernUI(APP_NAME)
        except Exception as e:
            print(f"Warning: Could not initialize modern UI: {e}")
            use_modern_gui = False
            use_gui = TK_SUPPORT
            ui = None
    
    # Fall back to regular tkinter UI
    if use_gui and not use_modern_gui:
        try:
            ui = UI(APP_NAME)
        except Exception:
            use_gui = False
            ui = None
    
    # If not using GUI, try Rich console
    if not use_modern_gui and not use_gui and RICH_SUPPORT:
        try:
            rich_ui = RichConsoleUI(APP_NAME)
            rich_ui.show_banner()
            rich_ui.show_welcome()
        except Exception:
            rich_ui = None
    
    # Create logger with appropriate UI backend
    logger = create_logger(args.log_dir, ui, rich_ui)
    
    # Create orchestrator
    orchestrator = SetupOrchestrator(config, logger, args)
    
    if (use_modern_gui or use_gui) and ui is not None:
        # GUI mode: show selection dialog then run
        cancel_event = threading.Event()
        ui.set_stop_callback(cancel_event.set)
        
        # Build registry for UI from config
        registry = config.get_categories()
        
        def on_start(selected_ids):
            steps = orchestrator.build_steps_from_selection(selected_ids)
            ui.set_stop_enabled(True)
            
            def _runner():
                try:
                    orchestrator.run_steps(steps, ui, cancel_event)
                finally:
                    ui.enqueue(('enable_close', None))
            
            t = threading.Thread(target=_runner, daemon=True)
            t.start()
        
        # Show selection dialog and enter UI loop
        ui.show_selection(registry, on_start)
        ui.run()
        
    elif rich_ui is not None:
        # Rich console mode with enhanced UI
        logger.info('Running in enhanced console mode with Rich UI')
        
        # For now, use default selections (could add interactive mode later)
        selected_ids = config.get_default_tool_ids()
        steps = orchestrator.build_steps_from_selection(selected_ids)
        
        # Run with Rich UI progress tracking
        total = len(steps)
        for i, (name, action) in enumerate(steps, start=1):
            rich_ui.start_step(i, total, name)
            logger.current_step = name
            
            try:
                action()
                rich_ui.complete_step(success=True)
            except Exception as e:
                logger.error(f"{name} failed: {e}")
                rich_ui.complete_step(success=False)
        
        logger.current_step = None
        rich_ui.show_completion(success=True)
        
    else:
        # Plain console mode fallback
        logger.warn('GUI and Rich UI not available; running in plain console mode.')
        selected_ids = config.get_default_tool_ids()
        steps = orchestrator.build_steps_from_selection(selected_ids)
        orchestrator.run_steps_console(steps)
    
    logger.success('Setup finished.')


if __name__ == '__main__':
    main()
