"""Package entry-point so the app can be launched with:
    python -m rose_engine_simulator
This simply calls the GUI bootstrap defined in ``main.py``.
"""
from .main import main

if __name__ == "__main__":
    main()
