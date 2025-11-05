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


def _select_ui(args):
    """Select and initialize the best available UI based on args and availability.
    Returns (ui, rich_ui, use_gui_flag)
    """
    if not args.no_gui:
        if CTK_SUPPORT:
            try:
                return ModernUI(APP_NAME), None, True
            except Exception as e:
                print(f"Warning: Could not initialize modern UI: {e}")
        if TK_SUPPORT:
            try:
                return UI(APP_NAME), None, True
            except Exception as e:
                print(f"Warning: Could not initialize Tk UI: {e}")
    # Console fallbacks
    if RICH_SUPPORT:
        try:
            rich = RichConsoleUI(APP_NAME)
            rich.show_banner()
            rich.show_welcome()
            return None, rich, False
        except Exception as e:
            print(f"Warning: Could not initialize Rich UI: {e}")
    return None, None, False


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Initialize configuration
    config = get_config()
    
    # Select UI
    ui, rich_ui, using_gui = _select_ui(args)
    
    # Create logger with appropriate UI backend
    logger = create_logger(args.log_dir, ui, rich_ui)

    # Validate config
    if not config.validate(logger):
        logger.error('Configuration invalid. Fix config/tools.json and try again.')
        return 2
    
    # Create orchestrator
    orchestrator = SetupOrchestrator(config, logger, args)
    
    if using_gui and ui is not None:
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
        
        selected_ids = config.get_default_tool_ids()
        steps = orchestrator.build_steps_from_selection(selected_ids)
        
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
