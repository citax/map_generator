"""
Configuration module for Topographic Map Generator.
Handles loading and accessing configuration settings.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for the application."""
    
    _instance = None
    _config_data = None  # Will be initialized in __init__
    _config_path = None  # Will be initialized in __init__
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize instance attributes here to avoid class-level mutable defaults
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._config_data = {}
            self._config_path = None
            self._initialized = True
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config file. Uses default if None.
        """
        if config_path is None:
            # Default config path relative to this module
            base_dir = Path(__file__).parent
            config_path = str(base_dir / "config.json")
        
        self._config_path = config_path
        
        try:
            with open(config_path, 'r') as f:
                self._config_data = json.load(f)
        except FileNotFoundError:
            self._config_data = self._get_default_config()
            self._save_config()
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in config file. Using defaults.")
            self._config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration values."""
        return {
            "application": {
                "name": "Topographic Map Generator",
                "version": "0.1.0",
                "window_width": 1200,
                "window_height": 800,
                "default_seed": None,
                "auto_generate": True
            },
            "terrain": {
                "map_width": 512,
                "map_height": 512,
                "scale": 50.0,
                "octaves": 6,
                "persistence": 0.5,
                "lacunarity": 2.0,
                "offset_x": 0.0,
                "offset_y": 0.0,
                "elevation_levels": 20,
                "min_elevation": 0.0,
                "max_elevation": 1000.0
            },
            "contour": {
                "line_color": "#4a4a4a",
                "line_width": 0.8,
                "fill_enabled": True,
                "colormap": "terrain",
                "contour_levels": 15,
                "show_elevation_labels": False
            },
            "features": {
                "mountains_enabled": True,
                "valleys_enabled": True,
                "rivers_enabled": False,
                "lakes_enabled": False,
                "vegetation_enabled": False
            },
            "display": {
                "dpi": 100,
                "figure_size_x": 10,
                "figure_size_y": 10,
                "background_color": "#f0f0f0",
                "grid_enabled": True
            },
            "seed": {
                "seed_length": 10,
                "seed_charset": "0123456789"
            }
        }
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        if self._config_path:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, 'w') as f:
                json.dump(self._config_data, f, indent=2)
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value(s).
        
        Args:
            section: Configuration section name.
            key: Specific key within section. If None, returns entire section.
            default: Default value if key not found.
        
        Returns:
            Configuration value or default.
        """
        if section not in self._config_data:
            return default
        
        if key is None:
            return self._config_data[section]
        
        return self._config_data[section].get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            section: Configuration section name.
            key: Key within section.
            value: Value to set.
        """
        if section not in self._config_data:
            self._config_data[section] = {}
        self._config_data[section][key] = value
    
    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """
        Update multiple values in a section.
        
        Args:
            section: Configuration section name.
            values: Dictionary of key-value pairs to update.
        """
        if section not in self._config_data:
            self._config_data[section] = {}
        self._config_data[section].update(values)
    
    def get_all(self) -> Dict[str, Any]:
        """Return all configuration data."""
        return self._config_data.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config_data = self._get_default_config()
    
    def get_terrain_settings(self) -> Dict[str, Any]:
        """Get terrain generation settings."""
        return self.get("terrain", None, {}).copy()
    
    def get_contour_settings(self) -> Dict[str, Any]:
        """Get contour rendering settings."""
        return self.get("contour", None, {}).copy()
    
    def get_display_settings(self) -> Dict[str, Any]:
        """Get display settings."""
        return self.get("display", None, {}).copy()


# Global config instance
config = Config()
