"""
Terrain Generator module for Topographic Map Generator.
Generates height maps using deterministic noise functions.
"""

import random
import math
from typing import Optional, List, Tuple
from .height_map import HeightMap


class PerlinNoise:
    """
    Deterministic Perlin noise generator.
    Uses a seed-based approach for reproducible results.
    """
    
    def __init__(self, seed: int):
        """
        Initialize Perlin noise generator with seed.
        
        Args:
            seed: Random seed for deterministic generation.
        """
        self.seed = seed
        self._permutation = self._generate_permutation(seed)
    
    def _generate_permutation(self, seed: int) -> List[int]:
        """Generate permutation table based on seed."""
        rng = random.Random(seed)
        perm = list(range(256))
        rng.shuffle(perm)
        # Duplicate for overflow
        return perm + perm
    
    def _fade(self, t: float) -> float:
        """Fade function for smooth interpolation."""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation."""
        return a + t * (b - a)
    
    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """Gradient function."""
        h = hash_val & 7
        u = x if h < 4 else y
        v = y if h < 4 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise(self, x: float, y: float) -> float:
        """
        Generate Perlin noise value at coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
        
        Returns:
            Noise value between -1.0 and 1.0.
        """
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        
        u = self._fade(xf)
        v = self._fade(yf)
        
        aa = self._permutation[self._permutation[xi] + yi]
        ab = self._permutation[self._permutation[xi] + yi + 1]
        ba = self._permutation[self._permutation[xi + 1] + yi]
        bb = self._permutation[self._permutation[xi + 1] + yi + 1]
        
        x1 = self._lerp(
            self._grad(aa, xf, yf),
            self._grad(ba, xf - 1, yf),
            u
        )
        x2 = self._lerp(
            self._grad(ab, xf, yf - 1),
            self._grad(bb, xf - 1, yf - 1),
            u
        )
        
        return self._lerp(x1, x2, v)


class TerrainGenerator:
    """
    Generates terrain height maps using noise functions.
    
    Supports mountains, valleys, and other elevation features.
    Deterministic output based on seed.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize terrain generator.
        
        Args:
            seed: Random seed. If None, a random seed is generated.
        """
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        
        self.seed = seed
        self.rng = random.Random(seed)
        self.perlin = PerlinNoise(seed)
    
    def generate(self, width: int, height: int,
                 scale: float = 50.0,
                 octaves: int = 6,
                 persistence: float = 0.5,
                 lacunarity: float = 2.0,
                 offset_x: float = 0.0,
                 offset_y: float = 0.0,
                 min_elevation: float = 0.0,
                 max_elevation: float = 1000.0,
                 sea_level: float = 0.0) -> HeightMap:
        """
        Generate a terrain height map.
        
        Args:
            width: Map width.
            height: Map height.
            scale: Noise scale (smaller = more zoomed in).
            octaves: Number of noise layers.
            persistence: Amplitude multiplier per octave.
            lacunarity: Frequency multiplier per octave.
            offset_x: X offset for noise.
            offset_y: Y offset for noise.
            min_elevation: Minimum elevation in meters.
            max_elevation: Maximum elevation in meters.
        
        Returns:
            Generated HeightMap.
        """
        height_map = HeightMap(width, height, min_elevation, max_elevation)
        
        # Generate base terrain using multi-octave noise
        for y in range(height):
            for x in range(width):
                amplitude = 1.0
                frequency = 1.0
                noise_value = 0.0
                
                for _ in range(octaves):
                    sample_x = (x + offset_x) / scale * frequency
                    sample_y = (y + offset_y) / scale * frequency
                    
                    noise_value += self.perlin.noise(sample_x, sample_y) * amplitude
                    
                    amplitude *= persistence
                    frequency *= lacunarity
                
                # Normalize from noise range to 0-1
                # Perlin noise returns -1 to 1, we want 0 to 1
                normalized = (noise_value + 1) / 2
                normalized = max(0.0, min(1.0, normalized))
                
                height_map.set_elevation(x, y, normalized)
        
        # Apply feature modifiers (pass sea_level for water)
        height_map = self._apply_features(height_map, sea_level)
        
        return height_map
    
    def _apply_features(self, height_map: HeightMap, sea_level: float = 0.0) -> HeightMap:
        """
        Apply terrain features like water/sea level.
        
        Args:
            height_map: Base height map.
            sea_level: Sea level (0.0-1.0). Areas below become water.
        
        Returns:
            Modified height map.
        """
        height_map.normalize()
        
        # Apply sea level - shift terrain so sea_level becomes 0
        if sea_level > 0:
            for y in range(height_map.height):
                for x in range(height_map.width):
                    elev = height_map.get_elevation(x, y)
                    # Shift so sea_level becomes 0
                    shifted = (elev - sea_level) / (1.0 - sea_level) if elev >= sea_level else 0.0
                    height_map.set_elevation(x, y, max(0.0, min(1.0, shifted)))
        
        return height_map
    
    def generate_mountain_range(self, height_map: HeightMap,
                                center_x: float, center_y: float,
                                radius: float, height: float) -> None:
        """
        Generate a mountain range at specified location.
        
        Args:
            height_map: Height map to modify.
            center_x: Center X coordinate.
            center_y: Center Y coordinate.
            radius: Mountain radius.
            height: Maximum height contribution.
        """
        for y in range(height_map.height):
            for x in range(height_map.width):
                dx = x - center_x
                dy = y - center_y
                dist = math.sqrt(dx * dx + dy * dy)
                
                if dist < radius:
                    # Gaussian-like falloff
                    falloff = math.exp(-(dist / radius) ** 2 * 3)
                    current = height_map.get_elevation(x, y)
                    new_elev = current + height * falloff
                    height_map.set_elevation(x, y, min(1.0, new_elev))
    
    def generate_valley(self, height_map: HeightMap,
                        start_x: float, start_y: float,
                        end_x: float, end_y: float,
                        width: float, depth: float) -> None:
        """
        Generate a valley between two points.
        
        Args:
            height_map: Height map to modify.
            start_x: Start X coordinate.
            start_y: Start Y coordinate.
            end_x: End X coordinate.
            end_y: End Y coordinate.
            width: Valley width.
            depth: Valley depth (0.0-1.0).
        """
        for y in range(height_map.height):
            for x in range(height_map.width):
                # Calculate distance to line segment
                dx = end_x - start_x
                dy = end_y - start_y
                
                if dx == 0 and dy == 0:
                    continue
                
                t = max(0, min(1, ((x - start_x) * dx + (y - start_y) * dy) / (dx * dx + dy * dy)))
                nearest_x = start_x + t * dx
                nearest_y = start_y + t * dy
                
                dist = math.sqrt((x - nearest_x) ** 2 + (y - nearest_y) ** 2)
                
                if dist < width:
                    falloff = 1.0 - (dist / width)
                    current = height_map.get_elevation(x, y)
                    new_elev = current - depth * falloff
                    height_map.set_elevation(x, y, max(0.0, new_elev))
    
    @staticmethod
    def seed_to_int(seed_input: str) -> int:
        """
        Convert a string seed to an integer.
        
        Args:
            seed_input: String seed value.
        
        Returns:
            Integer seed value.
        """
        try:
            return int(seed_input)
        except ValueError:
            # Hash the string to get an integer
            return hash(seed_input) % (2**32)
    
    @staticmethod
    def generate_random_seed(length: int = 10) -> str:
        """
        Generate a random seed string.
        
        Args:
            length: Length of seed string.
        
        Returns:
            Random seed string.
        """
        chars = "0123456789"
        return ''.join(random.choices(chars, k=length))
