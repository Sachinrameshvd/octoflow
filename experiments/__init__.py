"""Experiments and ablations package for OctopusBrain."""

from experiments.baselines import (
    AlwaysLocalBaseline,
    DenseCentralizedBaseline,
    SynchronousFullCommBaseline,
)

__all__ = [
    "DenseCentralizedBaseline",
    "SynchronousFullCommBaseline",
    "AlwaysLocalBaseline",
]
