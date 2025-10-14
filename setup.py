#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holmes VM Setup - Main entry point
Modular, extensible forensics VM setup tool
"""

import sys
import argparse
import threading

from holmes_vm.core.config import get_config
from holmes_vm.core.logger import create_logger, get_default_log_dir
from holmes_vm.core.orchestrator import SetupOrchestrator
from holmes_vm.ui.window import UI, is_tk_available


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
    
    # Determine if GUI is available and should be used
    use_gui = (not args.no_gui) and is_tk_available()
    
    ui = None
    if use_gui:
        try:
            ui = UI(APP_NAME)
        except Exception:
            use_gui = False
            ui = None
    
    # Create logger
    logger = create_logger(args.log_dir, ui)
    
    # Create orchestrator
    orchestrator = SetupOrchestrator(config, logger, args)
    
    if use_gui and ui is not None:
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
    else:
        # Console mode: use default selections
        logger.warn('GUI not available; running in console mode.')
        selected_ids = config.get_default_tool_ids()
        steps = orchestrator.build_steps_from_selection(selected_ids)
        orchestrator.run_steps_console(steps)
    
    logger.success('Setup finished.')


if __name__ == '__main__':
    main()
