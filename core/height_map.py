"""
Height Map module for Topographic Map Generator.
Represents a 2D grid of elevation values.
"""

from typing import List, Tuple, Optional
import math


class HeightMap:
    """
    Represents a 2D height map for terrain elevation data.
    
    Attributes:
        width: Map width in pixels/units.
        height: Map height in pixels/units.
        data: 2D list of elevation values (0.0 to 1.0 normalized).
        min_elevation: Minimum elevation value.
        max_elevation: Maximum elevation value.
    """
    
    def __init__(self, width: int, height: int, 
                 min_elevation: float = 0.0, 
                 max_elevation: float = 1000.0):
        """
        Initialize a height map.
        
        Args:
            width: Map width.
            height: Map height.
            min_elevation: Minimum elevation in meters.
            max_elevation: Maximum elevation in meters.
        """
        self.width = width
        self.height = height
        self.min_elevation = min_elevation
        self.max_elevation = max_elevation
        self.data: List[List[float]] = [[0.0] * width for _ in range(height)]
    
    def get_elevation(self, x: int, y: int) -> float:
        """
        Get elevation at specific coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
        
        Returns:
            Elevation value (normalized 0.0-1.0).
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.data[y][x]
        return 0.0
    
    def set_elevation(self, x: int, y: int, value: float) -> None:
        """
        Set elevation at specific coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            value: Elevation value (normalized 0.0-1.0).
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.data[y][x] = max(0.0, min(1.0, value))
    
    def get_real_elevation(self, x: int, y: int) -> float:
        """
        Get real-world elevation in meters.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
        
        Returns:
            Elevation in meters.
        """
        normalized = self.get_elevation(x, y)
        return self.min_elevation + normalized * (self.max_elevation - self.min_elevation)
    
    def get_elevation_levels(self, num_levels: int) -> List[float]:
        """
        Get elevation level values for contour lines.
        
        Args:
            num_levels: Number of contour levels.
        
        Returns:
            List of elevation values (normalized 0.0-1.0).
        """
        if num_levels <= 1:
            return [0.5]
        
        step = 1.0 / (num_levels - 1)
        return [i * step for i in range(num_levels)]
    
    def normalize(self) -> None:
        """Normalize all elevation values to 0.0-1.0 range."""
        if not self.data or not self.data[0]:
            return
        
        min_val = min(min(row) for row in self.data)
        max_val = max(max(row) for row in self.data)
        
        if max_val - min_val == 0:
            return
        
        for y in range(self.height):
            for x in range(self.width):
                self.data[y][x] = (self.data[y][x] - min_val) / (max_val - min_val)
    
    def get_stats(self) -> dict:
        """
        Get statistics about the height map.
        
        Returns:
            Dictionary containing min, max, mean, and other stats.
        """
        if not self.data or not self.data[0]:
            return {}
        
        all_values = [val for row in self.data for val in row]
        return {
            "min": min(all_values),
            "max": max(all_values),
            "mean": sum(all_values) / len(all_values),
            "width": self.width,
            "height": self.height,
            "real_min_m": self.min_elevation,
            "real_max_m": self.max_elevation
        }
    
    def copy(self) -> 'HeightMap':
        """Create a copy of the height map."""
        new_map = HeightMap(self.width, self.height, 
                          self.min_elevation, self.max_elevation)
        for y in range(self.height):
            for x in range(self.width):
                new_map.data[y][x] = self.data[y][x]
        return new_map
