"""
Core module for Topographic Map Generator.
Contains terrain generation and map data structures.
"""

from .terrain_generator import TerrainGenerator
from .height_map import HeightMap

__all__ = ['TerrainGenerator', 'HeightMap']
