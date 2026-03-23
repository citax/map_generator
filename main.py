"""
Main Application Entry Point for Topographic Map Generator.

This module handles application initialization, seed management,
and coordinates between core modules.
"""

import random
import sys
from typing import Optional, Dict, Any

from .config import config
from .core import TerrainGenerator, HeightMap
from .render import ContourRenderer


class MapGeneratorApp:
    """
    Main application class for the Topographic Map Generator.
    
    Handles initialization, map generation, and coordinates
    between terrain generation and rendering modules.
    """
    
    def __init__(self, seed: Optional[str] = None):
        """
        Initialize the application.
        
        Args:
            seed: Optional seed value. If None, generates random seed.
        """
        self._seed: Optional[int] = None
        self._seed_string: Optional[str] = None
        self._height_map: Optional[HeightMap] = None
        self._terrain_generator: Optional[TerrainGenerator] = None
        self._renderer: Optional[ContourRenderer] = None
        
        # Load configuration
        self._load_config()
        
        # Initialize seed
        self._init_seed(seed)
        
        # Initialize modules
        self._init_modules()
    
    def _load_config(self) -> None:
        """Load application configuration."""
        self._config = config.get_all()
    
    def _init_seed(self, seed_input: Optional[str]) -> None:
        """
        Initialize seed value.
        
        If no seed provided, generates a random one and displays it.
        
        Args:
            seed_input: User-provided seed string or None.
        """
        if seed_input is not None and seed_input.strip():
            # Use provided seed
            self._seed_string = seed_input.strip()
            self._seed = TerrainGenerator.seed_to_int(self._seed_string)
            print(f"Using provided seed: {self._seed_string}")
            print(f"Seed integer value: {self._seed}")
        else:
            # Generate random seed
            seed_length = config.get("seed", "seed_length", 10)
            self._seed_string = TerrainGenerator.generate_random_seed(seed_length)
            self._seed = TerrainGenerator.seed_to_int(self._seed_string)
            
            print("=" * 50)
            print("TOPOGRAPHIC MAP GENERATOR")
            print("=" * 50)
            print(f"Generated random seed: {self._seed_string}")
            print(f"Seed integer value: {self._seed}")
            print(f"NOTE: Save this seed to recreate the same map!")
            print("=" * 50)
    
    def _init_modules(self) -> None:
        """Initialize terrain generator and renderer."""
        self._terrain_generator = TerrainGenerator(seed=self._seed)
        self._renderer = ContourRenderer(config=self._config)
    
    @property
    def seed(self) -> int:
        """Get the current seed as integer."""
        return self._seed
    
    @property
    def seed_string(self) -> str:
        """Get the current seed as string."""
        return self._seed_string
    
    @property
    def height_map(self) -> Optional[HeightMap]:
        """Get the current height map."""
        return self._height_map
    
    def generate_map(self) -> HeightMap:
        """
        Generate a terrain height map using current configuration.
        
        Returns:
            Generated HeightMap.
        """
        # Get the entire terrain section
        terrain_config = self._config.get("terrain")
        if terrain_config is None:
            terrain_config = {}
        
        self._height_map = self._terrain_generator.generate(
            width=terrain_config.get("map_width", 512),
            height=terrain_config.get("map_height", 512),
            scale=terrain_config.get("scale", 50.0),
            octaves=terrain_config.get("octaves", 6),
            persistence=terrain_config.get("persistence", 0.5),
            lacunarity=terrain_config.get("lacunarity", 2.0),
            offset_x=terrain_config.get("offset_x", 0.0),
            offset_y=terrain_config.get("offset_y", 0.0),
            min_elevation=terrain_config.get("min_elevation", 0.0),
            max_elevation=terrain_config.get("max_elevation", 1000.0),
            sea_level=terrain_config.get("sea_level", 0.0)
        )
        
        return self._height_map
    
    def render_map(self, **kwargs) -> 'plt.Figure':
        """
        Render the current height map as a contour plot.
        
        Args:
            **kwargs: Override rendering settings.
        
        Returns:
            Matplotlib Figure object.
        """
        if self._height_map is None:
            self.generate_map()
        
        # Get the entire contour and display sections
        contour_config = self._config.get("contour")
        if contour_config is None:
            contour_config = {}
        display_config = self._config.get("display")
        if display_config is None:
            display_config = {}
        
        render_kwargs = {
            "contour_levels": contour_config.get("contour_levels", 15),
            "colormap": contour_config.get("colormap", "terrain"),
            "line_color": contour_config.get("line_color", "#4a4a4a"),
            "line_width": contour_config.get("line_width", 0.8),
            "fill_enabled": contour_config.get("fill_enabled", True),
            "show_labels": contour_config.get("show_elevation_labels", False),
            "figure_size": (display_config.get("figure_size_x", 10),
                           display_config.get("figure_size_y", 10)),
            "dpi": display_config.get("dpi", 100),
        }
        
        # Override with any provided kwargs
        render_kwargs.update(kwargs)
        
        return self._renderer.render(self._height_map, **render_kwargs)
    
    def render_ascii(self) -> str:
        """
        Render a simple ASCII representation of the map.
        
        Returns:
            ASCII art string.
        """
        if self._height_map is None:
            self.generate_map()
        
        return self._renderer.render_simple_ascii(self._height_map)
    
    def get_map_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current map.
        
        Returns:
            Dictionary of statistics.
        """
        if self._height_map is None:
            self.generate_map()
        
        return self._renderer.get_elevation_statistics(self._height_map)
    
    def set_seed(self, seed: str) -> None:
        """
        Set a new seed and reinitialize.
        
        Args:
            seed: New seed value.
        """
        self._init_seed(seed)
        self._init_modules()
        self._height_map = None
    
    def regenerate(self) -> HeightMap:
        """
        Regenerate the map with the same seed.
        
        Returns:
            Newly generated HeightMap.
        """
        self._init_modules()
        return self.generate_map()


def main(seed: Optional[str] = None) -> MapGeneratorApp:
    """
    Main entry point for the application.
    
    Args:
        seed: Optional seed value.
    
    Returns:
        Initialized MapGeneratorApp instance.
    """
    app = MapGeneratorApp(seed=seed)
    
    # Auto-generate if configured
    if config.get("application", "auto_generate", True):
        print("\nGenerating initial map...")
        app.generate_map()
        
        # Display stats
        stats = app.get_map_stats()
        print("\nMap Statistics:")
        print(f"  Size: {stats.get('width', 0)}x{stats.get('height', 0)}")
        print(f"  Min elevation: {stats.get('min', 0):.3f}")
        print(f"  Max elevation: {stats.get('max', 0):.3f}")
        print(f"  Mean elevation: {stats.get('mean', 0):.3f}")
        
        if 'terrain_distribution' in stats:
            dist = stats['terrain_distribution']
            print(f"  Lowland: {dist['lowland_percent']}%")
            print(f"  Midland: {dist['midland_percent']}%")
            print(f"  Highland: {dist['highland_percent']}%")
    
    return app


if __name__ == "__main__":
    # Parse command line arguments
    seed_arg = None
    if len(sys.argv) > 1:
        seed_arg = sys.argv[1]
    
    app = main(seed=seed_arg)
    
    # Print ASCII preview
    print("\nASCII Preview:")
    print(app.render_ascii())
