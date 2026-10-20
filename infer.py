"""Convenience root entrypoint for OctopusBrain inference.

Usage:
    python infer.py --episodes 2 --render terminal
    python infer.py --checkpoint checkpoints/best_octopus_brain.pt --render ascii
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from experiments.infer import main

if __name__ == "__main__":
    main()
