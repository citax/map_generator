"""
Contour Renderer module for Topographic Map Generator.
Renders height maps as topographic contour plots.
"""

import io
from typing import Optional, Tuple, List
import math

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for embedding
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    np = None

from ..core.height_map import HeightMap


class ContourRenderer:
    """
    Renders topographic contour maps from height data.
    
    Provides visually clear contour rendering with customizable
    appearance settings.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize contour renderer.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self._figure = None
        self._axes = None
    
    def render(self, height_map: HeightMap,
               contour_levels: int = 15,
               colormap: str = "terrain",
               line_color: str = "#4a4a4a",
               line_width: float = 0.8,
               fill_enabled: bool = True,
               show_labels: bool = False,
               figure_size: Tuple[float, float] = (10, 10),
               dpi: int = 100) -> 'plt.Figure':
        """
        Render a height map as a contour plot.
        
        Args:
            height_map: Height map to render.
            contour_levels: Number of contour levels.
            colormap: Matplotlib colormap name.
            line_color: Color for contour lines.
            line_width: Width of contour lines.
            fill_enabled: Whether to fill contours.
            show_labels: Whether to show elevation labels.
            figure_size: Size of the figure (width, height).
            dpi: DPI for rendering.
        
        Returns:
            Matplotlib Figure object.
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for contour rendering. "
                            "Install with: pip install matplotlib numpy")
        
        # Create figure and axes
        fig, ax = plt.subplots(figsize=figure_size, dpi=dpi)
        self._figure = fig
        self._axes = ax
        
        # Prepare data
        data = np.array(height_map.data)
        
        # Create coordinate grid
        x = np.linspace(0, height_map.width, height_map.width)
        y = np.linspace(0, height_map.height, height_map.height)
        X, Y = np.meshgrid(x, y)
        
        # Calculate contour levels
        if contour_levels > 0:
            levels = np.linspace(0, 1, contour_levels)
        else:
            levels = 15
        
        # Render contours
        if fill_enabled:
            contourf = ax.contourf(X, Y, data, levels=levels, cmap=colormap, alpha=0.8)
        
        # Contour lines
        contours = ax.contour(X, Y, data, levels=levels, colors=line_color, 
                             linewidths=line_width)
        
        # Add labels if requested
        if show_labels:
            ax.clabel(contours, inline=True, fontsize=8, fmt='%.2f')
        
        # Styling
        ax.set_title("Topographic Map", fontsize=14, fontweight='bold')
        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        ax.set_aspect('equal')
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add colorbar
        if fill_enabled:
            cbar = plt.colorbar(contourf, ax=ax, shrink=0.8)
            cbar.set_label('Elevation (normalized)', rotation=270, labelpad=15)
        
        plt.tight_layout()
        
        return fig
    
    def render_to_bytes(self, height_map: HeightMap, **kwargs) -> bytes:
        """
        Render height map and return as PNG bytes.
        
        Args:
            height_map: Height map to render.
            **kwargs: Additional arguments passed to render().
        
        Returns:
            PNG image data as bytes.
        """
        fig = self.render(height_map, **kwargs)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        
        plt.close(fig)
        
        return buf.read()
    
    def render_simple_ascii(self, height_map: HeightMap,
                           width: int = 80,
                           height: int = 40) -> str:
        """
        Render a simple ASCII representation of the height map.
        Useful for debugging and terminal display.
        Matches UI orientation (y increases upward).
        
        Args:
            height_map: Height map to render.
            width: Output width in characters.
            height: Output height in characters.
        
        Returns:
            ASCII art string.
        """
        # Characters from low to high elevation
        chars = " .:-=+*#%@"
        
        output = []
        output.append("=" * (width + 2))
        
        # Iterate y from bottom to top to match matplotlib's upward y-axis
        step_y = max(1, height_map.height // height)
        step_x = max(1, height_map.width // width)
        
        for y_idx in range(height):
            y = height_map.height - 1 - (y_idx * step_y)
            if y < 0:
                y = 0
            
            line = "|"
            for x_idx in range(width):
                x = x_idx * step_x
                if x >= height_map.width:
                    x = height_map.width - 1
                
                elev = height_map.get_elevation(x, y)
                char_idx = min(int(elev * len(chars)), len(chars) - 1)
                line += chars[char_idx]
            
            line += "|"
            output.append(line)
        
        output.append("=" * (width + 2))
        return "\n".join(output)
    
    def get_elevation_statistics(self, height_map: HeightMap) -> dict:
        """
        Get elevation statistics for display.
        
        Args:
            height_map: Height map to analyze.
        
        Returns:
            Dictionary of statistics.
        """
        stats = height_map.get_stats()
        
        # Calculate additional stats
        data = [val for row in height_map.data for val in row]
        
        # Categorize terrain
        low = sum(1 for v in data if v < 0.3) / len(data) * 100
        mid = sum(1 for v in data if 0.3 <= v < 0.7) / len(data) * 100
        high = sum(1 for v in data if v >= 0.7) / len(data) * 100
        
        stats['terrain_distribution'] = {
            'lowland_percent': round(low, 1),
            'midland_percent': round(mid, 1),
            'highland_percent': round(high, 1)
        }
        
        return stats
    
    def close(self) -> None:
        """Close the current figure."""
        if self._figure is not None and MATPLOTLIB_AVAILABLE:
            plt.close(self._figure)
            self._figure = None
            self._axes = None
