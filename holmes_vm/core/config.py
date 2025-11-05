#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for Holmes VM
"""

import os
import json
from typing import Dict, List, Any, Optional


class Config:
    """Configuration manager for Holmes VM setup"""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            # Default to config directory in project root
            self.config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'config'
            )
        else:
            self.config_dir = config_dir
            
        self.repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # Update to scripts/windows for PowerShell module
        self.module_path = os.path.join(self.repo_dir, 'scripts', 'windows', 'Holmes.Common.psm1')
        self.util_dir = os.path.join(self.repo_dir, 'scripts', 'windows')
        # Assets moved inside package
        self.assets_dir = os.path.join(self.repo_dir, 'holmes_vm', 'assets')
        
        # Load tools configuration
        self.tools_config = self._load_tools_config()
        # Optional versions map at top-level: { "versions": { "wireshark": "x.y.z" } }
        self.versions = self.tools_config.get('versions', {})
        
    def _load_tools_config(self) -> Dict[str, Any]:
        """Load tools configuration from JSON"""
        config_file = os.path.join(self.config_dir, 'tools.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"categories": []}
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all tool categories"""
        return self.tools_config.get('categories', [])
    
    def get_tool_by_id(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Find a tool by its ID"""
        for category in self.get_categories():
            for item in category.get('items', []):
                if item.get('id') == tool_id:
                    return item
        return None
    
    def get_all_tool_ids(self) -> List[str]:
        """Get list of all tool IDs"""
        tool_ids: List[str] = []
        for category in self.get_categories():
            for item in category.get('items', []):
                tool_ids.append(item.get('id'))
        return tool_ids
    
    def get_default_tool_ids(self) -> List[str]:
        """Get list of tools that are selected by default"""
        tool_ids: List[str] = []
        for category in self.get_categories():
            for item in category.get('items', []):
                if item.get('default', False):
                    tool_ids.append(item.get('id'))
        return tool_ids

    # New helpers for versioning and normalized lookups
    def get_version_for(self, tool_id: str) -> Optional[str]:
        """Return an optional version string for a tool from top-level versions map or per-item."""
        item = self.get_tool_by_id(tool_id) or {}
        # Prefer per-item version, fallback to global versions dict
        return item.get('version') or self.versions.get(tool_id)

    def get_choco_params(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Normalized chocolatey installer parameters (name, version)."""
        item = self.get_tool_by_id(tool_id)
        if not item or item.get('installer_type') != 'chocolatey':
            return None
        return {
            'name': item.get('package_name'),
            'tool_name': item.get('name'),
            'version': self.get_version_for(tool_id)
        }

    def get_powershell_params(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Normalized powershell installer parameters (script, function, args)."""
        item = self.get_tool_by_id(tool_id)
        if not item or item.get('installer_type') != 'powershell':
            return None
        return {
            'script_path': item.get('script_path'),
            'function_name': item.get('function_name'),
            'tool_name': item.get('name'),
            'args': item.get('args', '')
        }

    def get_function_installer_id(self, tool_id: str) -> Optional[str]:
        """Return the registered function installer id for a tool."""
        item = self.get_tool_by_id(tool_id)
        if not item or item.get('installer_type') != 'function':
            return None
        return item.get('installer')

    def validate(self, logger: Optional[Any] = None) -> bool:
        """Validate tools.json structure and report issues. Returns True if valid enough to proceed."""
        ok = True
        cats = self.get_categories()
        if not isinstance(cats, list):
            if logger:
                logger.error('Invalid config: categories must be a list')
            return False
        for cidx, cat in enumerate(cats):
            if 'id' not in cat or 'name' not in cat:
                ok = False
                if logger:
                    logger.warn(f"Category at index {cidx} is missing 'id' or 'name'")
            items = cat.get('items', [])
            if not isinstance(items, list):
                ok = False
                if logger:
                    logger.error(f"Category '{cat.get('id', '?')}' has invalid 'items' (must be list)")
                continue
            for item in items:
                iid = item.get('id')
                iname = item.get('name')
                itype = item.get('installer_type')
                if not iid or not iname or not itype:
                    ok = False
                    if logger:
                        logger.error(f"Item missing required fields (id/name/installer_type): {item}")
                    continue
                if itype == 'chocolatey' and not item.get('package_name'):
                    ok = False
                    if logger:
                        logger.error(f"[{iid}] chocolatey item missing 'package_name'")
                if itype == 'powershell' and (not item.get('script_path') or not item.get('function_name')):
                    ok = False
                    if logger:
                        logger.error(f"[{iid}] powershell item missing 'script_path' or 'function_name'")
                if itype == 'function' and not item.get('installer'):
                    ok = False
                    if logger:
                        logger.error(f"[{iid}] function item missing 'installer'")
        return ok


# Global config instance
_config = None


def get_config() -> 'Config':
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config
