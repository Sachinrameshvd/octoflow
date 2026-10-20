"""Experiments and ablations package for OctopusBrain."""

from experiments.baselines import (
    DenseCentralizedBaseline,
    SynchronousFullCommBaseline,
    AlwaysLocalBaseline,
)

__all__ = [
    "DenseCentralizedBaseline",
    "SynchronousFullCommBaseline",
    "AlwaysLocalBaseline",
]
