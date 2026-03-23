"""
Topographic Map Generator - Main Entry Point

This module allows running the application with:
    python -m topo_map_generator

The desktop UI is launched by default. Use command line arguments
to customize behavior.
"""

import sys
import argparse


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Topographic Map Generator - Generate bird's eye view topographic maps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m topo_map_generator                    # Launch desktop UI with random seed
  python -m topo_map_generator --seed 1234567890  # Launch UI with specific seed
  python -m topo_map_generator --cli              # Run in terminal mode (ASCII preview)
  python -m topo_map_generator --cli --seed 123   # Terminal mode with seed
"""
    )
    
    parser.add_argument(
        "--seed", "-s",
        type=str,
        default=None,
        help="Seed value for map generation (10-digit number or any string)"
    )
    
    parser.add_argument(
        "--cli", "-c",
        action="store_true",
        help="Run in terminal/CLI mode instead of desktop UI"
    )
    
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Show ASCII preview in terminal (implies --cli)"
    )
    
    args = parser.parse_args()
    
    # If --ascii is specified, imply --cli
    if args.ascii:
        args.cli = True
    
    if args.cli:
        # Terminal/CLI mode
        from topo_map_generator.main import main as cli_main
        app = cli_main(seed=args.seed)
        
        if args.ascii or not args.seed:
            print("\nASCII Preview:")
            print(app.render_ascii())
    else:
        # Desktop UI mode (default)
        try:
            from topo_map_generator.ui import run_app
            run_app(seed=args.seed)
        except (ImportError, RuntimeError) as e:
            print(f"Cannot start desktop UI: {e}")
            print("\nFalling back to terminal mode...")
            from topo_map_generator.main import main as cli_main
            app = cli_main(seed=args.seed)
            print("\nASCII Preview:")
            print(app.render_ascii())
        except Exception as e:
            # Handle other errors (display errors, etc.)
            import traceback
            print(f"Unexpected error starting desktop UI: {e}")
            print("Full traceback:")
            traceback.print_exc()
            print("\nFalling back to terminal mode...")
            from topo_map_generator.main import main as cli_main
            app = cli_main(seed=args.seed)
            print("\nASCII Preview:")
            print(app.render_ascii())


if __name__ == "__main__":
    main()
