import sys
import os

# Set up proper module imports
# This is to ensure the application can be run from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import our enhanced MainWindow
from rose_engine_simulator.gui.main_window import MainWindow

def main():
    """Main entry point for the Rose Engine Simulator application."""
    # Note: High-DPI scaling is enabled by default in newer PyQt6 versions
    # No need to set attributes manually
    
    app = QApplication(sys.argv)
    
    # Create the main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
