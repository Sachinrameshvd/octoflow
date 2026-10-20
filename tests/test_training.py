"""Unit tests for OctopusTrainer, rollout collection, and checkpoint persistence."""

import os
import tempfile
import pytest
import torch
from octopus_brain.config import OctopusBrainConfig, EnvConfig
from octopus_brain.brain import OctopusBrain
from octopus_brain.trainer import OctopusTrainer
from envs.reach_and_avoid import ReachAndAvoidEnv


def test_trainer_collect_episode_and_gae():
    config = OctopusBrainConfig(n_modules=4, hidden_dim=32, message_dim=16)
    env_config = EnvConfig(n_arms=4, max_steps=15)
    env = ReachAndAvoidEnv(env_config)
    model = OctopusBrain(config)

    trainer = OctopusTrainer(model=model, env=env, config=config, lr=0.003)
    traj = trainer.collect_episode(seed=42)

    assert "log_probs" in traj
    assert "values" in traj
    assert "returns" in traj
    assert "report_probs" in traj
    assert traj["log_probs"].shape[2] == 4  # N=4 modules
    assert traj["returns"].shape == traj["log_probs"].shape


def test_trainer_train_step_gradient_update():
    config = OctopusBrainConfig(n_modules=4, hidden_dim=32, message_dim=16)
    env_config = EnvConfig(n_arms=4, max_steps=10)
    env = ReachAndAvoidEnv(env_config)
    model = OctopusBrain(config)

    trainer = OctopusTrainer(model=model, env=env, config=config, lr=0.003)
    traj = trainer.collect_episode(seed=123)

    p_before = list(model.parameters())[0].clone()
    metrics = trainer.train_step(traj)
    p_after = list(model.parameters())[0].clone()

    assert "total_loss" in metrics
    assert "policy_loss" in metrics
    assert "value_loss" in metrics
    assert "dual_lambda" in metrics
    assert not torch.isnan(torch.tensor(metrics["total_loss"]))
    assert not torch.allclose(p_before, p_after)  # Confirms real neural weight optimization


def test_trainer_evaluation():
    config = OctopusBrainConfig(n_modules=4, hidden_dim=32, message_dim=16)
    env_config = EnvConfig(n_arms=4, max_steps=10)
    env = ReachAndAvoidEnv(env_config)
    model = OctopusBrain(config)

    trainer = OctopusTrainer(model=model, env=env, config=config)
    eval_res = trainer.evaluate(n_episodes=3, seed=777)

    assert "mean_reward" in eval_res
    assert "mean_report_rate" in eval_res
    assert "mean_coalition_size" in eval_res
    assert 0.0 <= eval_res["mean_report_rate"] <= 1.0


def test_trainer_checkpoint_save_and_load():
    config = OctopusBrainConfig(n_modules=4, hidden_dim=32, message_dim=16)
    env_config = EnvConfig(n_arms=4, max_steps=10)
    env = ReachAndAvoidEnv(env_config)
    model = OctopusBrain(config)

    trainer = OctopusTrainer(model=model, env=env, config=config)

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt_path = os.path.join(tmpdir, "model_test.pt")
        trainer.save_checkpoint(ckpt_path)
        assert os.path.exists(ckpt_path)

        new_model = OctopusBrain(config)
        new_trainer = OctopusTrainer(model=new_model, env=env, config=config)
        new_trainer.load_checkpoint(ckpt_path)

        # Verify weights match
        for p1, p2 in zip(model.parameters(), new_model.parameters()):
            assert torch.allclose(p1, p2)


def test_trainer_ppo_multi_epoch_step():
    config = OctopusBrainConfig(n_modules=4, hidden_dim=32, message_dim=16)
    env_config = EnvConfig(n_arms=4, max_steps=10)
    env = ReachAndAvoidEnv(env_config)
    model = OctopusBrain(config)

    trainer = OctopusTrainer(
        model=model,
        env=env,
        config=config,
        lr=0.003,
        algorithm="ppo",
        ppo_epochs=3,
        clip_eps=0.2,
        normalize_advantages=True,
    )
    traj = trainer.collect_episode(seed=42)
    assert "advantages" in traj
    assert "obs_list" in traj
    assert "actions_list" in traj

    metrics = trainer.train_step(traj)
    assert "total_loss" in metrics
    assert "policy_loss" in metrics
    assert not torch.isnan(torch.tensor(metrics["total_loss"]))
