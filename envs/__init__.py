"""Environments for OctopusBrain experiments."""

from envs.curriculum import CurriculumEnv, CurriculumScheduler
from envs.hunting_env import CooperativeHuntingEnv
from envs.reach_and_avoid import ReachAndAvoidEnv

__all__ = ["ReachAndAvoidEnv", "CooperativeHuntingEnv", "CurriculumEnv", "CurriculumScheduler"]
