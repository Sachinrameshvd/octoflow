"""Convenience root entrypoint for OctopusBrain training.

Usage:
    python train.py --episodes 150 --eval-every 25
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from experiments.train import main

if __name__ == "__main__":
    main()
