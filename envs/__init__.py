"""Environments for OctopusBrain experiments."""

from envs.reach_and_avoid import ReachAndAvoidEnv
from envs.hunting_env import CooperativeHuntingEnv
from envs.curriculum import CurriculumEnv, CurriculumScheduler

__all__ = ["ReachAndAvoidEnv", "CooperativeHuntingEnv", "CurriculumEnv", "CurriculumScheduler"]
