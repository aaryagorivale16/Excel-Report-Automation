import sys
import os

# Ensure the src module is discoverable if run from root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.gui import run_app

if __name__ == "__main__":
    run_app()
