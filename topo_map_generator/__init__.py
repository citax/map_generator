"""
Topographic Map Generator

A deterministic, seed-based topographic map generator for
bird's eye view visualization of geographic elevation features.

Features:
- Deterministic generation (same seed = same map)
- Visually clear contour rendering
- Modular architecture for future features
- Desktop GUI application

Usage:
    from topo_map_generator import MapGeneratorApp
    
    # Generate with random seed
    app = MapGeneratorApp()
    
    # Generate with specific seed
    app = MapGeneratorApp(seed="1234567890")
    
    # Generate map
    height_map = app.generate_map()
    
    # Render as contour plot
    fig = app.render_map()
    
    # Run desktop application
    from topo_map_generator.ui import run_app
    run_app()
"""

from typing import Optional

from .main import MapGeneratorApp, main
from .config import config
from .core import TerrainGenerator, HeightMap
from .render import ContourRenderer

__version__ = "0.1.0"
__all__ = [
    'MapGeneratorApp',
    'main',
    'config',
    'TerrainGenerator',
    'HeightMap',
    'ContourRenderer',
    'run_app'
]

# Convenience function for running the desktop app
def run_app(seed: Optional[str] = None):
    """
    Launch the desktop application.
    
    Args:
        seed: Optional seed value to initialize the map.
    """
    from .ui import run_app as _run_app
    _run_app(seed=seed)
