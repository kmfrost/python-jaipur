#!/usr/bin/env python3
"""
Self-play training for stronger Jaipur RL agent.

Key improvements over basic training:
1. Self-play: Train against copies of the model
2. Larger network: More capacity for complex strategies
3. Opponent pool: Mix of random + self-play for diversity
4. Periodic opponent updates: Keep improving against stronger versions
5. Longer training with checkpoints

Usage:
    python train_selfplay.py                    # Train from scratch
    python train_selfplay.py --continue_from models/jaipur_ppo_xxx  # Continue from checkpoint
    python train_selfplay.py --timesteps 2000000  # Train longer
"""

import argparse
import os
import sys
from datetime import datetime
from copy import deepcopy

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.monitor import Monitor

from JaipurSelfPlayEnv import JaipurSelfPlayEnv
from JaipurEnv import JaipurEnv


class SelfPlayCallback(BaseCallback):
    """
    Callback to:
    1. Update opponent model periodically
    2. Track win rate against random player
    3. Save checkpoints
    """

    def __init__(
        self,
        update_freq=50000,
        eval_freq=25000,
        n_eval_episodes=100,
        save_path="models",
        verbose=1
    ):
        super().__init__(verbose)
        self.update_freq = update_freq
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.save_path = save_path

        self.opponent_update_count = 0
        self.best_win_rate = 0.0
        self.win_rates = []

    def _on_step(self):
        # Update opponent model periodically
        if self.n_calls % self.update_freq == 0:
            self._update_opponent()

        # Evaluate against random player periodically
        if self.n_calls % self.eval_freq == 0:
            win_rate = self._evaluate_vs_random()
            self.win_rates.append((self.n_calls, win_rate))

            if self.verbose:
                print(f"Step {self.n_calls}: Win rate vs Random = {win_rate:.1%}")

            # Save best model
            if win_rate > self.best_win_rate:
                self.best_win_rate = win_rate
                best_path = os.path.join(self.save_path, "jaipur_selfplay_best")
                self.model.save(best_path)
                if self.verbose:
                    print(f"  New best! Saved to {best_path}")

        return True

    def _update_opponent(self):
        """Update the opponent model in all environments."""
        self.opponent_update_count += 1

        # Create a copy of current model for opponent
        # We need to save and reload to get a true copy
        temp_path = os.path.join(self.save_path, "_temp_opponent")
        self.model.save(temp_path)
        opponent_model = PPO.load(temp_path)

        # Update opponent in all envs
        for env in self.training_env.envs:
            if hasattr(env, 'env'):
                # Wrapped env (e.g., Monitor)
                if hasattr(env.env, 'set_opponent_model'):
                    env.env.set_opponent_model(opponent_model)
            elif hasattr(env, 'set_opponent_model'):
                env.set_opponent_model(opponent_model)

        if self.verbose:
            print(f"Step {self.n_calls}: Updated opponent (update #{self.opponent_update_count})")

        # Cleanup temp file
        if os.path.exists(temp_path + ".zip"):
            os.remove(temp_path + ".zip")

    def _evaluate_vs_random(self):
        """Evaluate current model against random player."""
        env = JaipurEnv()  # Uses RandomPlayer opponent
        wins = 0

        for _ in range(self.n_eval_episodes):
            obs, info = env.reset()
            done = False

            while not done:
                action_mask = info.get("action_mask", np.ones(13))
                action, _ = self.model.predict(obs, deterministic=True)

                if action_mask[action] == 0:
                    valid_actions = np.where(action_mask == 1)[0]
                    action = np.random.choice(valid_actions)

                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated

            if reward > 0.5:
                wins += 1

        env.close()
        return wins / self.n_eval_episodes


def make_selfplay_env(opponent_model=None, random_prob=0.3):
    """Create a self-play environment."""
    def _init():
        env = JaipurSelfPlayEnv(
            opponent_model=opponent_model,
            random_opponent_prob=random_prob
        )
        return Monitor(env)
    return _init


def train(
    timesteps=1000000,
    n_envs=8,
    save_path="models",
    continue_from=None,
    random_opponent_prob=0.3
):
    """Train with self-play."""
    print(f"Training with self-play for {timesteps} timesteps...")
    print(f"Using {n_envs} parallel environments")
    print(f"Random opponent probability: {random_opponent_prob}")

    os.makedirs(save_path, exist_ok=True)

    # Create vectorized environment
    # Use DummyVecEnv to allow opponent model updates (SubprocVecEnv can't access envs)
    env = DummyVecEnv([make_selfplay_env(None, random_opponent_prob) for _ in range(n_envs)])

    # Larger network for more complex strategies
    policy_kwargs = dict(
        net_arch=dict(
            pi=[256, 256, 128],  # Policy network: 3 layers
            vf=[256, 256, 128]   # Value network: 3 layers
        )
    )

    if continue_from:
        print(f"Continuing from {continue_from}...")
        model = PPO.load(continue_from, env=env)
        # Update hyperparameters for fine-tuning
        model.learning_rate = 1e-4  # Lower LR for fine-tuning
    else:
        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=128,  # Larger batch
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.02,  # More exploration
            policy_kwargs=policy_kwargs,
            tensorboard_log="./tensorboard_logs/",
        )

    # Callbacks
    selfplay_callback = SelfPlayCallback(
        update_freq=50000,   # Update opponent every 50k steps
        eval_freq=25000,     # Evaluate every 25k steps
        n_eval_episodes=100,
        save_path=save_path,
        verbose=1
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=100000,
        save_path=save_path,
        name_prefix="jaipur_selfplay_checkpoint"
    )

    # Train
    model.learn(
        total_timesteps=timesteps,
        callback=[selfplay_callback, checkpoint_callback],
        progress_bar=True,
    )

    # Save final model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = os.path.join(save_path, f"jaipur_selfplay_{timestamp}")
    model.save(final_path)
    print(f"Final model saved to {final_path}")

    # Final evaluation
    print("\nFinal evaluation vs RandomPlayer...")
    final_win_rate = selfplay_callback._evaluate_vs_random()
    print(f"Final win rate: {final_win_rate:.1%}")

    env.close()

    return model, final_path


def main():
    parser = argparse.ArgumentParser(description="Self-play training for Jaipur")
    parser.add_argument("--timesteps", type=int, default=1000000,
                        help="Number of training timesteps (default: 1M)")
    parser.add_argument("--envs", type=int, default=8,
                        help="Number of parallel environments (default: 8)")
    parser.add_argument("--continue_from", type=str, default=None,
                        help="Path to model to continue training from")
    parser.add_argument("--random_prob", type=float, default=0.3,
                        help="Probability of using random opponent (default: 0.3)")

    args = parser.parse_args()

    train(
        timesteps=args.timesteps,
        n_envs=args.envs,
        continue_from=args.continue_from,
        random_opponent_prob=args.random_prob
    )


if __name__ == "__main__":
    main()
