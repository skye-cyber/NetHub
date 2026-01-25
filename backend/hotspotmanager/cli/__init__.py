import sys
from pathlib import Path


version = "1.0.3"


# Get the absolute path to the parent directory
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
