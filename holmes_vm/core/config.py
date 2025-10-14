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
        self.module_path = os.path.join(self.repo_dir, 'modules', 'Holmes.Common.psm1')
        self.util_dir = os.path.join(self.repo_dir, 'util')
        self.assets_dir = os.path.join(self.repo_dir, 'assets')
        
        # Load tools configuration
        self.tools_config = self._load_tools_config()
        
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
        tool_ids = []
        for category in self.get_categories():
            for item in category.get('items', []):
                tool_ids.append(item.get('id'))
        return tool_ids
    
    def get_default_tool_ids(self) -> List[str]:
        """Get list of tools that are selected by default"""
        tool_ids = []
        for category in self.get_categories():
            for item in category.get('items', []):
                if item.get('default', False):
                    tool_ids.append(item.get('id'))
        return tool_ids


# Global config instance
_config = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config
