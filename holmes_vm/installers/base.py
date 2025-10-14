#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base installer class and registry for Holmes VM tools
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..core.logger import Logger
from ..core.config import Config


class BaseInstaller(ABC):
    """Base class for all installers"""
    
    def __init__(self, config: Config, logger: Logger, args: Any):
        self.config = config
        self.logger = logger
        self.args = args
    
    @abstractmethod
    def install(self) -> bool:
        """Execute installation. Returns True on success, False on failure"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get installer name"""
        pass
    
    def should_force_reinstall(self) -> bool:
        """Check if should force reinstall"""
        return getattr(self.args, 'force_reinstall', False)
    
    def is_what_if_mode(self) -> bool:
        """Check if running in what-if mode"""
        return getattr(self.args, 'what_if', False)


class InstallerRegistry:
    """Registry of available installers"""
    
    def __init__(self):
        self._installers: Dict[str, type] = {}
    
    def register(self, installer_id: str, installer_class: type):
        """Register an installer"""
        self._installers[installer_id] = installer_class
    
    def get_installer(self, installer_id: str, config: Config, logger: Logger, args: Any) -> Optional[BaseInstaller]:
        """Get an installer instance"""
        installer_class = self._installers.get(installer_id)
        if installer_class:
            return installer_class(config, logger, args)
        return None
    
    def list_installers(self):
        """List all registered installers"""
        return list(self._installers.keys())


# Global registry
_registry = InstallerRegistry()


def get_registry() -> InstallerRegistry:
    """Get global installer registry"""
    return _registry


def register_installer(installer_id: str):
    """Decorator to register an installer"""
    def decorator(cls):
        _registry.register(installer_id, cls)
        return cls
    return decorator
