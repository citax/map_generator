"""
Main Window module for Topographic Map Generator.
Desktop GUI application using tkinter.
"""

from __future__ import annotations

import io
from typing import Optional, TYPE_CHECKING

# Check for tkinter availability first
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None  # type: ignore
    ttk = None  # type: ignore
    messagebox = None  # type: ignore
    filedialog = None  # type: ignore

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from ..config import config
from ..main import MapGeneratorApp

# Type hints for type checkers
if TYPE_CHECKING:
    import tkinter as tk


class MainWindow:
    """
    Main application window for the Topographic Map Generator.
    
    Provides a desktop GUI for generating and viewing topographic maps.
    """
    
    def __init__(self, root: tk.Tk, initial_seed: Optional[str] = None):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window.
            initial_seed: Optional seed value to initialize the map.
        """
        self.root = root
        self.app: Optional[MapGeneratorApp] = None
        self.current_image = None
        self.current_photo = None
        self._initial_seed = initial_seed
        
        # Load config
        self._load_config()
        
        # Setup window
        self._setup_window()
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        
        # Initialize application with seed (or random if None)
        self._init_app()
    
    def _load_config(self) -> None:
        """Load configuration values."""
        # Get the entire application section (no key argument needed)
        app_config = config.get("application")
        # Handle case where section might not exist
        if app_config is None:
            app_config = {}
        self.window_width = app_config.get("window_width", 1200)
        self.window_height = app_config.get("window_height", 800)
        self.app_name = app_config.get("name", "Topographic Map Generator")
        self.version = app_config.get("version", "0.1.0")
    
    def _setup_window(self) -> None:
        """Configure the main window."""
        self.root.title(f"{self.app_name} v{self.version}")
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.minsize(800, 600)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_menu(self) -> None:
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Map", command=self._new_map)
        file_menu.add_command(label="Save Image...", command=self._save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Generate menu
        generate_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Generate", menu=generate_menu)
        generate_menu.add_command(label="Generate Map", command=self._generate_map)
        generate_menu.add_command(label="Regenerate (Same Seed)", command=self._regenerate_map)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Settings...", command=self._open_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Reset All to Defaults", command=self._reset_settings_to_defaults)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_toolbar(self) -> None:
        """Create the toolbar with controls."""
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Seed input
        ttk.Label(toolbar, text="Seed:").pack(side=tk.LEFT, padx=5)
        
        self.seed_var = tk.StringVar()
        self.seed_entry = ttk.Entry(toolbar, textvariable=self.seed_var, width=20)
        self.seed_entry.pack(side=tk.LEFT, padx=5)
        self.seed_entry.bind('<Return>', lambda e: self._generate_map())
        
        # Generate button
        self.generate_btn = ttk.Button(toolbar, text="Generate", command=self._generate_map)
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Random seed button
        self.random_btn = ttk.Button(toolbar, text="Random Seed", command=self._new_map)
        self.random_btn.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Preset dropdown
        ttk.Label(toolbar, text="Preset:").pack(side=tk.LEFT, padx=5)
        self.preset_var = tk.StringVar(value="Mountains")
        self.preset_combo = ttk.Combobox(toolbar, textvariable=self.preset_var,
                                          values=preset_manager.get_preset_names(),
                                          state="readonly", width=15)
        self.preset_combo.pack(side=tk.LEFT, padx=5)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_toolbar_preset_selected)
        
        # Save preset button
        self.save_preset_btn = ttk.Button(toolbar, text="Save Preset", command=self._save_preset_from_toolbar)
        self.save_preset_btn.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Save button
        self.save_btn = ttk.Button(toolbar, text="Save Image", command=self._save_image)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Stats button
        self.stats_btn = ttk.Button(toolbar, text="Show Stats", command=self._show_stats)
        self.stats_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_main_area(self) -> None:
        """Create the main display area."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas with scrollbar for map display
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#f0f0f0", highlightthickness=1)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=v_scroll.set)
        
        h_scroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=h_scroll.set)
        
        # Info panel
        info_frame = ttk.Frame(main_frame, width=200)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        info_frame.pack_propagate(False)
        
        # Seed display
        ttk.Label(info_frame, text="Current Seed:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.seed_display = ttk.Label(info_frame, text="-", wraplength=180)
        self.seed_display.pack(anchor=tk.W, pady=(0, 15))
        
        # Stats display
        ttk.Label(info_frame, text="Statistics:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        self.stats_text = tk.Text(info_frame, height=15, width=25, wrap=tk.WORD, 
                                   font=("Courier", 9), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready", padding="5")
        self.status_label.pack(side=tk.LEFT)
        
        self.seed_status = ttk.Label(self.status_bar, text="", padding="5")
        self.seed_status.pack(side=tk.RIGHT)
    
    def _init_app(self) -> None:
        """Initialize the application with seed (or random if None)."""
        if self._initial_seed:
            self.app = MapGeneratorApp(seed=self._initial_seed)
        else:
            self.app = MapGeneratorApp(seed=None)
        
        self.seed_var.set(self.app.seed_string)
        self.seed_display.config(text=self.app.seed_string)
        self.seed_status.config(text=f"Seed: {self.app.seed_string}")
        
        # Generate initial map
        self._generate_map()
    
    def _generate_map(self) -> None:
        """Generate a new map with the current seed."""
        try:
            seed_input = self.seed_var.get().strip()
            
            if seed_input:
                # Check if seed changed
                if self.app is None or seed_input != self.app.seed_string:
                    self.app = MapGeneratorApp(seed=seed_input)
            else:
                # Generate with random seed
                self.app = MapGeneratorApp(seed=None)
                self.seed_var.set(self.app.seed_string)
            
            self.seed_display.config(text=self.app.seed_string)
            self.seed_status.config(text=f"Seed: {self.app.seed_string}")
            self.status_label.config(text="Generating map...")
            self.root.update()
            
            # Generate the map
            self.app.generate_map()
            
            # Render and display
            self._display_map()
            
            # Update stats
            self._update_stats()
            
            self.status_label.config(text="Map generated successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate map: {str(e)}")
            self.status_label.config(text="Error generating map")
    
    def _new_map(self) -> None:
        """Generate a new map with a random seed."""
        self.seed_var.set("")
        self._generate_map()
    
    def _regenerate_map(self) -> None:
        """Regenerate the map with the same seed."""
        if self.app:
            self.app.regenerate()
            self._display_map()
            self._update_stats()
            self.status_label.config(text="Map regenerated")
    
    def _display_map(self) -> None:
        """Render and display the map in the canvas."""
        if not self.app or not self.app.height_map:
            return
        
        try:
            # Check for PIL availability
            if not PIL_AVAILABLE:
                # Fallback to ASCII display
                ascii_art = self.app.render_ascii()
                self.canvas.delete("all")
                self.canvas.create_text(10, 10, text=ascii_art, anchor=tk.NW,
                                        font=("Courier", 8), fill="black")
                self.status_label.config(text="Showing ASCII preview (install PIL for better display)")
                return
            
            # Render the map using matplotlib
            fig = self.app.render_map()
            
            # Convert to PIL Image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            
            from matplotlib import pyplot as plt
            plt.close(fig)
            
            image = Image.open(buf)
            self.current_image = image
            
            # Create PhotoImage
            self.current_photo = ImageTk.PhotoImage(image)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.current_photo, anchor=tk.NW)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            
            self.status_label.config(text="Map rendered with contour lines")
            
        except ImportError as e:
            # Matplotlib not available - show ASCII fallback
            ascii_art = self.app.render_ascii()
            self.canvas.delete("all")
            self.canvas.create_text(10, 10, text=ascii_art, anchor=tk.NW,
                                    font=("Courier", 8), fill="black")
            self.status_label.config(text="Contour rendering requires: pip install matplotlib numpy")
            
        except Exception as e:
            messagebox.showerror("Render Error", f"Failed to render map: {str(e)}")
            self.status_label.config(text="Render error - check console")
    
    def _update_stats(self) -> None:
        """Update the statistics display."""
        if not self.app:
            return
        
        try:
            stats = self.app.get_map_stats()
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            
            stats_text = f"""Size: {stats.get('width', 0)}x{stats.get('height', 0)}

Elevation:
  Min: {stats.get('min', 0):.3f}
  Max: {stats.get('max', 0):.3f}
  Mean: {stats.get('mean', 0):.3f}

Terrain Distribution:"""
            
            if 'terrain_distribution' in stats:
                dist = stats['terrain_distribution']
                stats_text += f"""
  Lowland: {dist['lowland_percent']}%
  Midland: {dist['midland_percent']}%
  Highland: {dist['highland_percent']}%
"""
            
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception:
            pass
    
    def _save_image(self) -> None:
        """Save the current map as an image file."""
        if not self.app:
            messagebox.showwarning("Warning", "No map to save")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ],
            title="Save Map As"
        )
        
        if filepath:
            try:
                if self.current_image:
                    self.current_image.save(filepath)
                else:
                    # Render and save
                    fig = self.app.render_map()
                    fig.savefig(filepath, format='png', bbox_inches='tight', dpi=150)
                    from matplotlib import pyplot as plt
                    plt.close(fig)
                
                self.status_label.config(text=f"Saved to {filepath}")
                messagebox.showinfo("Success", f"Map saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def _show_stats(self) -> None:
        """Show detailed statistics in a dialog."""
        if not self.app:
            return
        
        stats = self.app.get_map_stats()
        
        msg = f"""Map Statistics

Seed: {self.app.seed_string}
Size: {stats.get('width', 0)} x {stats.get('height', 0)}

Elevation Range:
  Minimum: {stats.get('min', 0):.4f}
  Maximum: {stats.get('max', 0):.4f}
  Mean: {stats.get('mean', 0):.4f}
  
Terrain Distribution:"""
        
        if 'terrain_distribution' in stats:
            dist = stats['terrain_distribution']
            msg += f"""
  Lowland (< 0.3): {dist['lowland_percent']}%
  Midland (0.3-0.7): {dist['midland_percent']}%
  Highland (> 0.7): {dist['highland_percent']}%
"""
        
        messagebox.showinfo("Map Statistics", msg)
    
    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            f"{self.app_name}\n"
            f"Version {self.version}\n\n"
            "A topographic map generator with\n"
            "deterministic seed-based generation.\n\n"
            "Features:\n"
            "• Seed-based deterministic maps\n"
            "• Contour rendering\n"
            "• Modular architecture\n\n"
            "© 2024"
        )
    
    # ==================== Settings Panel Methods ====================
    
    def _open_settings(self) -> None:
        """Open unified settings dialog."""
        SettingsDialog(self.root, self)
    
    def _reset_settings_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Reset all settings to default values?"):
            config.reset_to_defaults()
            self.status_label.config(text="Settings reset to defaults")
            self._generate_map()
    
    def _apply_all_settings(self, settings: dict) -> None:
        """
        Apply all settings and regenerate map.
        
        Args:
            settings: Dictionary containing terrain and contour settings
        """
        if "terrain" in settings:
            config.update_section("terrain", settings["terrain"])
        if "contour" in settings:
            config.update_section("contour", settings["contour"])
        self.status_label.config(text="Settings applied")
        self._generate_map()
    
    def _apply_preset(self, preset_name: str) -> None:
        """
        Apply a preset and regenerate map.
        
        Args:
            preset_name: Name of the preset to apply
        """
        preset = preset_manager.get_preset(preset_name)
        if "terrain" in preset:
            config.update_section("terrain", preset["terrain"])
        if "contour" in preset:
            config.update_section("contour", preset["contour"])
        self._generate_map()
    
    def _on_toolbar_preset_selected(self, event=None) -> None:
        """Handle preset selection from toolbar."""
        preset_name = self.preset_var.get()
        self._apply_preset(preset_name)
    
    def _save_preset_from_toolbar(self) -> None:
        """Save current settings as a custom preset from toolbar."""
        from tkinter import simpledialog
        name = simpledialog.askstring("Save Preset", "Enter preset name:")
        if name:
            settings = {
                "terrain": config.get_terrain_settings(),
                "contour": config.get_contour_settings()
            }
            if preset_manager.save_preset(name, settings):
                # Update preset dropdowns
                preset_names = preset_manager.get_preset_names()
                self.preset_combo['values'] = preset_names
                if hasattr(self, 'preset_combo_dialog'):
                    self.preset_combo_dialog['values'] = preset_names
                self.preset_var.set(name)
                messagebox.showinfo("Success", f"Preset '{name}' saved!")
            else:
                messagebox.showwarning("Error", "Could not save preset (name may be reserved)")


# ==================== Preset Manager ====================

class PresetManager:
    """Manages preset configurations for terrain and render settings."""
    
    # Default presets - tuned for realistic elevation behavior
    # Scale: high=flat/smooth (zoomed out), low=rough/detailed (zoomed in)
    # Octaves: low=smooth, high=detailed
    # Persistence: low=flat, high=varied/harsh elevation changes
    # Sea level: 0.0=no water, 0.3=30% water coverage
    DEFAULT_PRESETS = {
        "Plains": {
            # Very flat - high scale (zoomed out), low octaves, low persistence
            "terrain": {"scale": 250.0, "octaves": 2, "persistence": 0.2, "lacunarity": 2.0, "sea_level": 0.0},
            "contour": {"colormap": "viridis", "contour_levels": 8, "fill_enabled": True}
        },
        "Hills": {
            # Gentle rolling hills - medium scale, medium octaves, medium persistence
            "terrain": {"scale": 100.0, "octaves": 4, "persistence": 0.4, "lacunarity": 2.0, "sea_level": 0.0},
            "contour": {"colormap": "terrain", "contour_levels": 12, "fill_enabled": True}
        },
        "Mountains": {
            # Harsh elevation changes - low scale (zoomed in), high octaves, high persistence
            "terrain": {"scale": 35.0, "octaves": 7, "persistence": 0.7, "lacunarity": 2.2, "sea_level": 0.0},
            "contour": {"colormap": "terrain", "contour_levels": 20, "fill_enabled": True}
        },
        "Desert": {
            # Mostly flat with some dunes - high scale, low octaves, low persistence
            "terrain": {"scale": 200.0, "octaves": 3, "persistence": 0.25, "lacunarity": 1.8, "sea_level": 0.0},
            "contour": {"colormap": "plasma", "contour_levels": 8, "fill_enabled": True}
        },
        "Arctic": {
            # Icy plateaus with some variation - high scale, medium octaves
            "terrain": {"scale": 180.0, "octaves": 4, "persistence": 0.35, "lacunarity": 2.0, "sea_level": 0.0},
            "contour": {"colormap": "gray", "contour_levels": 10, "fill_enabled": True}
        },
        "Volcanic": {
            # Very rough with harsh peaks - low scale, high octaves, high persistence
            "terrain": {"scale": 25.0, "octaves": 8, "persistence": 0.75, "lacunarity": 2.5, "sea_level": 0.0},
            "contour": {"colormap": "plasma", "contour_levels": 25, "fill_enabled": True}
        },
        "Sea": {
            # Mostly water with islands - high sea level, flat terrain
            "terrain": {"scale": 150.0, "octaves": 3, "persistence": 0.3, "lacunarity": 2.0, "sea_level": 0.4},
            "contour": {"colormap": "terrain", "contour_levels": 10, "fill_enabled": True}
        },
        "Lake": {
            # Inland lake with surrounding hills - medium sea level
            "terrain": {"scale": 80.0, "octaves": 4, "persistence": 0.45, "lacunarity": 2.0, "sea_level": 0.25},
            "contour": {"colormap": "terrain", "contour_levels": 12, "fill_enabled": True}
        },
        "River": {
            # River valley - medium scale with some water
            "terrain": {"scale": 60.0, "octaves": 5, "persistence": 0.5, "lacunarity": 2.0, "sea_level": 0.15},
            "contour": {"colormap": "terrain", "contour_levels": 15, "fill_enabled": True}
        }
    }
    
    PRESETS_FILE = "presets.json"
    
    def __init__(self):
        """Initialize preset manager."""
        self.custom_presets = {}
        self._load_custom_presets()
    
    def _get_presets_path(self) -> str:
        """Get the path for presets file."""
        import os
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), self.PRESETS_FILE)
    
    def _load_custom_presets(self) -> None:
        """Load custom presets from file."""
        try:
            import json
            path = self._get_presets_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.custom_presets = json.load(f)
        except Exception:
            self.custom_presets = {}
    
    def _save_custom_presets(self) -> None:
        """Save custom presets to file."""
        try:
            import json
            path = self._get_presets_path()
            with open(path, 'w') as f:
                json.dump(self.custom_presets, f, indent=2)
        except Exception:
            pass
    
    def get_all_presets(self) -> dict:
        """Get all presets (default + custom)."""
        presets = self.DEFAULT_PRESETS.copy()
        presets.update(self.custom_presets)
        return presets
    
    def get_preset_names(self) -> list:
        """Get list of all preset names."""
        return list(self.get_all_presets().keys())
    
    def get_preset(self, name: str) -> dict:
        """Get a specific preset by name."""
        return self.get_all_presets().get(name, self.DEFAULT_PRESETS["Mountains"])
    
    def save_preset(self, name: str, settings: dict) -> bool:
        """
        Save a custom preset.
        
        Args:
            name: Preset name
            settings: Settings dictionary with terrain and contour sections
        
        Returns:
            True if saved successfully
        """
        if not name or name in self.DEFAULT_PRESETS:
            return False
        self.custom_presets[name] = settings
        self._save_custom_presets()
        return True
    
    def delete_preset(self, name: str) -> bool:
        """Delete a custom preset."""
        if name in self.custom_presets:
            del self.custom_presets[name]
            self._save_custom_presets()
            return True
        return False


# Global preset manager
preset_manager = PresetManager()


# ==================== Settings Dialog Classes ====================

class SettingsDialog:
    """Unified settings dialog with terrain, render, and preset options."""
    
    # Default values
    DEFAULT_SCALE = 50.0
    DEFAULT_OCTAVES = 6
    DEFAULT_PERSISTENCE = 0.5
    DEFAULT_LACUNARITY = 2.0
    DEFAULT_COLORMAP = "terrain"
    DEFAULT_CONTOUR_LEVELS = 15
    DEFAULT_FILL_ENABLED = True
    
    # Ranges
    SCALE_MIN = 10
    SCALE_MAX = 200
    OCTAVES_MIN = 1
    OCTAVES_MAX = 10
    PERSISTENCE_MIN = 0.1
    PERSISTENCE_MAX = 0.9
    LACUNARITY_MIN = 1.0
    LACUNARITY_MAX = 4.0
    CONTOUR_LEVELS_MIN = 5
    CONTOUR_LEVELS_MAX = 30
    
    # Available colormaps
    COLORMAPS = ["terrain", "viridis", "plasma", "coolwarm", "gray"]
    
    def __init__(self, parent, main_window: MainWindow):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent window.
            main_window: Main application window.
        """
        self.parent = parent
        self.main_window = main_window
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("450x550")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Get current settings
        terrain_settings = config.get_terrain_settings()
        contour_settings = config.get_contour_settings()
        
        self.current_scale = terrain_settings.get("scale", self.DEFAULT_SCALE)
        self.current_octaves = terrain_settings.get("octaves", self.DEFAULT_OCTAVES)
        self.current_persistence = terrain_settings.get("persistence", self.DEFAULT_PERSISTENCE)
        self.current_lacunarity = terrain_settings.get("lacunarity", self.DEFAULT_LACUNARITY)
        self.current_colormap = contour_settings.get("colormap", self.DEFAULT_COLORMAP)
        self.current_contour_levels = contour_settings.get("contour_levels", self.DEFAULT_CONTOUR_LEVELS)
        self.current_fill_enabled = contour_settings.get("fill_enabled", self.DEFAULT_FILL_ENABLED)
        
        # Create widgets
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === Preset Section ===
        preset_frame = ttk.LabelFrame(main_frame, text="Preset", padding="10")
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(preset_frame, text="Preset:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.preset_var = tk.StringVar(value="Mountains")
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                          values=preset_manager.get_preset_names(),
                                          state="readonly", width=20)
        self.preset_combo.pack(side=tk.LEFT, padx=5)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)
        
        ttk.Button(preset_frame, text="Save Preset", command=self._save_preset).pack(side=tk.LEFT, padx=5)
        
        # === Map Size ===
        size_frame = ttk.LabelFrame(main_frame, text="Map Size", padding="10")
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        terrain_settings = config.get_terrain_settings()
        current_width = terrain_settings.get("map_width", 512)
        current_height = terrain_settings.get("map_height", 512)
        
        ttk.Label(size_frame, text="Width:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.map_width_var = tk.IntVar(value=current_width)
        width_scale = ttk.Scale(size_frame, from_=128, to=2048, variable=self.map_width_var,
                               orient=tk.HORIZONTAL, length=150, command=self._on_map_size_change)
        width_scale.grid(row=0, column=1, pady=3, padx=5)
        self.map_width_label = ttk.Label(size_frame, text=str(current_width), width=6)
        self.map_width_label.grid(row=0, column=2, padx=5)
        
        ttk.Label(size_frame, text="Height:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.map_height_var = tk.IntVar(value=current_height)
        height_scale = ttk.Scale(size_frame, from_=128, to=2048, variable=self.map_height_var,
                                orient=tk.HORIZONTAL, length=150, command=self._on_map_size_change)
        height_scale.grid(row=1, column=1, pady=3, padx=5)
        self.map_height_label = ttk.Label(size_frame, text=str(current_height), width=6)
        self.map_height_label.grid(row=1, column=2, padx=5)
        
        # === Terrain Settings ===
        terrain_frame = ttk.LabelFrame(main_frame, text="Terrain Settings", padding="10")
        terrain_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Scale
        ttk.Label(terrain_frame, text="Scale:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.scale_var = tk.DoubleVar(value=self.current_scale)
        self.scale_scale = ttk.Scale(terrain_frame, from_=self.SCALE_MIN, to=self.SCALE_MAX,
                                      variable=self.scale_var, orient=tk.HORIZONTAL, length=200,
                                      command=self._on_scale_change)
        self.scale_scale.grid(row=0, column=1, pady=3, padx=5)
        self.scale_label = ttk.Label(terrain_frame, text=f"{self.current_scale:.0f}", width=6)
        self.scale_label.grid(row=0, column=2, padx=5)
        
        # Octaves
        ttk.Label(terrain_frame, text="Octaves:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.octaves_var = tk.IntVar(value=self.current_octaves)
        self.octaves_scale = ttk.Scale(terrain_frame, from_=self.OCTAVES_MIN, to=self.OCTAVES_MAX,
                                        variable=self.octaves_var, orient=tk.HORIZONTAL, length=200,
                                        command=self._on_octaves_change)
        self.octaves_scale.grid(row=1, column=1, pady=3, padx=5)
        self.octaves_label = ttk.Label(terrain_frame, text=str(self.current_octaves), width=6)
        self.octaves_label.grid(row=1, column=2, padx=5)
        
        # Persistence
        ttk.Label(terrain_frame, text="Persistence:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.persistence_var = tk.DoubleVar(value=self.current_persistence)
        self.persistence_scale = ttk.Scale(terrain_frame, from_=self.PERSISTENCE_MIN, 
                                            to=self.PERSISTENCE_MAX, variable=self.persistence_var,
                                            orient=tk.HORIZONTAL, length=200,
                                            command=self._on_persistence_change)
        self.persistence_scale.grid(row=2, column=1, pady=3, padx=5)
        self.persistence_label = ttk.Label(terrain_frame, text=f"{self.current_persistence:.2f}", width=6)
        self.persistence_label.grid(row=2, column=2, padx=5)
        
        # Lacunarity
        ttk.Label(terrain_frame, text="Lacunarity:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.lacunarity_var = tk.DoubleVar(value=self.current_lacunarity)
        self.lacunarity_scale = ttk.Scale(terrain_frame, from_=self.LACUNARITY_MIN, 
                                          to=self.LACUNARITY_MAX, variable=self.lacunarity_var,
                                          orient=tk.HORIZONTAL, length=200,
                                          command=self._on_lacunarity_change)
        self.lacunarity_scale.grid(row=3, column=1, pady=3, padx=5)
        self.lacunarity_label = ttk.Label(terrain_frame, text=f"{self.current_lacunarity:.1f}", width=6)
        self.lacunarity_label.grid(row=3, column=2, padx=5)
        
        # === Render Settings ===
        render_frame = ttk.LabelFrame(main_frame, text="Render Settings", padding="10")
        render_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Colormap
        ttk.Label(render_frame, text="Colormap:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.colormap_var = tk.StringVar(value=self.current_colormap)
        colormap_combo = ttk.Combobox(render_frame, textvariable=self.colormap_var,
                                       values=self.COLORMAPS, state="readonly", width=15)
        colormap_combo.grid(row=0, column=1, pady=3, padx=5, sticky=tk.W)
        colormap_combo.bind("<<ComboboxSelected>>", self._on_colormap_change)
        
        # Contour levels
        ttk.Label(render_frame, text="Contour Levels:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.contour_levels_var = tk.IntVar(value=self.current_contour_levels)
        self.contour_scale = ttk.Scale(render_frame, from_=self.CONTOUR_LEVELS_MIN, 
                                        to=self.CONTOUR_LEVELS_MAX,
                                        variable=self.contour_levels_var, orient=tk.HORIZONTAL, 
                                        length=200, command=self._on_contour_change)
        self.contour_scale.grid(row=1, column=1, pady=3, padx=5)
        self.contour_levels_label = ttk.Label(render_frame, text=str(self.current_contour_levels), width=6)
        self.contour_levels_label.grid(row=1, column=2, padx=5)
        
        # Fill enabled
        ttk.Label(render_frame, text="Fill Contours:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.fill_enabled_var = tk.BooleanVar(value=self.current_fill_enabled)
        fill_check = ttk.Checkbutton(render_frame, variable=self.fill_enabled_var,
                                      command=self._on_fill_change)
        fill_check.grid(row=2, column=1, pady=3, padx=5, sticky=tk.W)
        
        # === Buttons ===
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="Reset Defaults", command=self._reset_defaults).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    # Auto-apply handlers
    def _on_map_size_change(self, value):
        config.update_section("terrain", {
            "map_width": int(self.map_width_var.get()),
            "map_height": int(self.map_height_var.get())
        })
        self.map_width_label.config(text=str(int(self.map_width_var.get())))
        self.map_height_label.config(text=str(int(self.map_height_var.get())))
        self.main_window._generate_map()
    
    def _on_scale_change(self, value):
        config.update_section("terrain", {"scale": float(value)})
        self.scale_label.config(text=f"{float(value):.0f}")
        self.main_window._generate_map()
    
    def _on_octaves_change(self, value):
        config.update_section("terrain", {"octaves": int(float(value))})
        self.octaves_label.config(text=str(int(float(value))))
        self.main_window._generate_map()
    
    def _on_persistence_change(self, value):
        config.update_section("terrain", {"persistence": float(value)})
        self.persistence_label.config(text=f"{float(value):.2f}")
        self.main_window._generate_map()
    
    def _on_lacunarity_change(self, value):
        config.update_section("terrain", {"lacunarity": float(value)})
        self.lacunarity_label.config(text=f"{float(value):.1f}")
        self.main_window._generate_map()
    
    def _on_colormap_change(self, event=None):
        config.update_section("contour", {"colormap": self.colormap_var.get()})
        self.main_window._generate_map()
    
    def _on_contour_change(self, value):
        config.update_section("contour", {"contour_levels": int(float(value))})
        self.contour_levels_label.config(text=str(int(float(value))))
        self.main_window._generate_map()
    
    def _on_fill_change(self):
        config.update_section("contour", {"fill_enabled": self.fill_enabled_var.get()})
        self.main_window._generate_map()
    
    def _on_preset_selected(self, event=None):
        """Handle preset selection."""
        preset_name = self.preset_var.get()
        preset = preset_manager.get_preset(preset_name)
        
        # Apply terrain settings
        if "terrain" in preset:
            config.update_section("terrain", preset["terrain"])
        # Apply contour settings
        if "contour" in preset:
            config.update_section("contour", preset["contour"])
        
        # Update UI values
        terrain = preset.get("terrain", {})
        contour = preset.get("contour", {})
        
        self.scale_var.set(terrain.get("scale", self.DEFAULT_SCALE))
        self.octaves_var.set(terrain.get("octaves", self.DEFAULT_OCTAVES))
        self.persistence_var.set(terrain.get("persistence", self.DEFAULT_PERSISTENCE))
        self.lacunarity_var.set(terrain.get("lacunarity", self.DEFAULT_LACUNARITY))
        self.colormap_var.set(contour.get("colormap", self.DEFAULT_COLORMAP))
        self.contour_levels_var.set(contour.get("contour_levels", self.DEFAULT_CONTOUR_LEVELS))
        self.fill_enabled_var.set(contour.get("fill_enabled", self.DEFAULT_FILL_ENABLED))
        
        # Update labels
        self.scale_label.config(text=f"{self.scale_var.get():.0f}")
        self.octaves_label.config(text=str(self.octaves_var.get()))
        self.persistence_label.config(text=f"{self.persistence_var.get():.2f}")
        self.lacunarity_label.config(text=f"{self.lacunarity_var.get():.1f}")
        self.contour_levels_label.config(text=str(self.contour_levels_var.get()))
        
        self.main_window._generate_map()
    
    def _save_preset(self):
        """Save current settings as a custom preset."""
        from tkinter import simpledialog
        name = simpledialog.askstring("Save Preset", "Enter preset name:")
        if name:
            settings = {
                "terrain": {
                    "scale": self.scale_var.get(),
                    "octaves": int(self.octaves_var.get()),
                    "persistence": self.persistence_var.get(),
                    "lacunarity": self.lacunarity_var.get()
                },
                "contour": {
                    "colormap": self.colormap_var.get(),
                    "contour_levels": int(self.contour_levels_var.get()),
                    "fill_enabled": self.fill_enabled_var.get()
                }
            }
            if preset_manager.save_preset(name, settings):
                # Update preset dropdown
                self.preset_combo['values'] = preset_manager.get_preset_names()
                self.preset_var.set(name)
                messagebox.showinfo("Success", f"Preset '{name}' saved!")
            else:
                messagebox.showwarning("Error", "Could not save preset (name may be reserved)")
    
    def _reset_defaults(self):
        """Reset all settings to defaults."""
        # Map size
        self.map_width_var.set(512)
        self.map_height_var.set(512)
        self.map_width_label.config(text="512")
        self.map_height_label.config(text="512")
        
        # Terrain
        self.scale_var.set(self.DEFAULT_SCALE)
        self.octaves_var.set(self.DEFAULT_OCTAVES)
        self.persistence_var.set(self.DEFAULT_PERSISTENCE)
        self.lacunarity_var.set(self.DEFAULT_LACUNARITY)
        
        # Render
        self.colormap_var.set(self.DEFAULT_COLORMAP)
        self.contour_levels_var.set(self.DEFAULT_CONTOUR_LEVELS)
        self.fill_enabled_var.set(self.DEFAULT_FILL_ENABLED)
        
        # Update labels
        self.scale_label.config(text=f"{self.DEFAULT_SCALE:.0f}")
        self.octaves_label.config(text=str(self.DEFAULT_OCTAVES))
        self.persistence_label.config(text=f"{self.DEFAULT_PERSISTENCE:.2f}")
        self.lacunarity_label.config(text=f"{self.DEFAULT_LACUNARITY:.1f}")
        self.contour_levels_label.config(text=str(self.DEFAULT_CONTOUR_LEVELS))
        
        # Apply defaults
        config.reset_to_defaults()
        self.main_window._generate_map()


def run_app(seed: Optional[str] = None) -> None:
    """
    Run the desktop application.
    
    Args:
        seed: Optional seed value to initialize the map.
    
    Raises:
        RuntimeError: If tkinter is not available.
    """
    if not TKINTER_AVAILABLE:
        raise RuntimeError(
            "tkinter is not available. Please install it to use the desktop UI.\n"
            "On Ubuntu/Debian: sudo apt-get install python3-tk\n"
            "On Fedora: sudo dnf install python3-tkinter\n"
            "On macOS: tkinter is usually included with Python\n"
            "On Windows: tkinter is included with Python\n\n"
            "Alternatively, use the CLI mode: python -m topo_map_generator --cli"
        )
    
    root = tk.Tk()
    app = MainWindow(root, initial_seed=seed)
    root.mainloop()
