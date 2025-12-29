#!/usr/bin/env python3
"""
Training script for Jaipur RL agent using Stable-Baselines3.

Usage:
    python train.py                    # Train with default settings
    python train.py --timesteps 500000 # Train for 500k timesteps
    python train.py --eval             # Evaluate a trained model
    python train.py --play             # Play against trained model
"""

import argparse
import os
import sys
from datetime import datetime

import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor

from JaipurEnv import JaipurEnv


class WinRateCallback(BaseCallback):
    """Callback to track win rate during training."""

    def __init__(self, eval_freq=10000, n_eval_episodes=100, verbose=1):
        super().__init__(verbose)
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.win_rates = []

    def _on_step(self):
        if self.n_calls % self.eval_freq == 0:
            win_rate = evaluate_win_rate(self.model, self.n_eval_episodes)
            self.win_rates.append((self.n_calls, win_rate))
            if self.verbose:
                print(f"Step {self.n_calls}: Win rate = {win_rate:.1%}")
        return True


def evaluate_win_rate(model, n_episodes=100):
    """Evaluate the model's win rate against RandomPlayer."""
    env = JaipurEnv()
    wins = 0
    losses = 0
    ties = 0

    for _ in range(n_episodes):
        obs, info = env.reset()
        done = False
        while not done:
            action_mask = info.get("action_mask", np.ones(13))
            action, _ = model.predict(obs, deterministic=True)

            # If action is masked, choose a valid one
            if action_mask[action] == 0:
                valid_actions = np.where(action_mask == 1)[0]
                action = np.random.choice(valid_actions)

            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

        # Determine outcome from final reward
        if reward > 0.5:
            wins += 1
        elif reward < -0.5:
            losses += 1
        else:
            ties += 1

    env.close()
    return wins / n_episodes


def make_env():
    """Create a Jaipur environment."""
    def _init():
        return Monitor(JaipurEnv())
    return _init


def train(timesteps=100000, n_envs=4, save_path="models"):
    """Train a PPO agent on Jaipur."""
    print(f"Training PPO agent for {timesteps} timesteps...")
    print(f"Using {n_envs} parallel environments")

    # Create vectorized environment
    env = SubprocVecEnv([make_env() for _ in range(n_envs)])

    # Create evaluation environment
    eval_env = Monitor(JaipurEnv())

    # Create the model
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,  # Encourage exploration
        tensorboard_log="./tensorboard_logs/",
    )

    # Create callbacks
    win_rate_callback = WinRateCallback(eval_freq=10000, n_eval_episodes=50)

    # Train
    model.learn(
        total_timesteps=timesteps,
        callback=win_rate_callback,
        progress_bar=True,
    )

    # Save the model
    os.makedirs(save_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(save_path, f"jaipur_ppo_{timestamp}")
    model.save(model_path)
    print(f"Model saved to {model_path}")

    # Final evaluation
    print("\nFinal evaluation...")
    final_win_rate = evaluate_win_rate(model, n_episodes=200)
    print(f"Final win rate: {final_win_rate:.1%}")

    env.close()
    eval_env.close()

    return model, model_path


def evaluate(model_path, n_episodes=200):
    """Evaluate a trained model."""
    print(f"Loading model from {model_path}...")
    model = PPO.load(model_path)

    print(f"Evaluating over {n_episodes} episodes...")
    win_rate = evaluate_win_rate(model, n_episodes)
    print(f"Win rate: {win_rate:.1%}")

    return win_rate


def play_against_model(model_path):
    """Play interactively against the trained model."""
    print(f"Loading model from {model_path}...")
    model = PPO.load(model_path)

    # Import Player for human play
    from Player import Player
    from GameEngine import GameEngine

    print("\nYou are Player 1. The RL agent is Player 2.")
    print("Action codes: (c)amels, (g)rab, (s)ell, (t)rade\n")

    game_engine = GameEngine()
    human_player = Player(game_engine)

    # Create a wrapper to translate between game engine and model
    env = JaipurEnv()

    while not game_engine.is_done():
        if game_engine.whos_turn == 0:
            # Human's turn
            human_player.take_action()
        else:
            # RL agent's turn
            # We need to get observation from agent's perspective (player 1)
            # This is tricky - the env assumes we're player 0
            # For now, use RandomPlayer logic with model predictions

            # Get state and create observation
            state = game_engine.get_state()

            # Build observation (same as JaipurEnv._get_observation but for current player)
            from collections import Counter
            obs = []
            hand_counts = Counter(state['my_hand'])
            for card_type in env.CARD_TYPES:
                obs.append(hand_counts.get(card_type, 0) / 12.0)
            market_counts = Counter(state['market'])
            for card_type in env.CARD_TYPES:
                obs.append(market_counts.get(card_type, 0) / 5.0)
            for good_type in env.GOOD_TYPES:
                tokens = state['tokens_left'].get(good_type, [])
                obs.append(len(tokens) / 9.0)
            for bonus_size in [3, 4, 5]:
                obs.append(state['bonus_num_left'].get(bonus_size, 0) / 7.0)
            obs.append(sum(state['my_tokens']) / 150.0)
            obs.append(state['enemy_num_goods'] / 7.0)
            obs.append(state['enemy_num_camels'] / 11.0)
            obs.append(sum(state['enemy_tokens']) / 150.0)
            obs.append(state['num_deck'] / 40.0)
            obs = np.array(obs, dtype=np.float32)

            # Get action from model
            action, _ = model.predict(obs, deterministic=True)

            # Execute action
            my_hand = state['my_hand']
            market = state['market']

            success = False
            if action == 0:
                success = game_engine.do_action("c")
            elif 1 <= action <= 5:
                grab_idx = action - 1
                if grab_idx < len(market):
                    success = game_engine.do_action("g", grab_idx=grab_idx)
            elif 6 <= action <= 11:
                good_type = env.GOOD_TYPES[action - 6]
                sell_idx = [i for i, x in enumerate(my_hand) if x == good_type]
                if sell_idx:
                    success = game_engine.do_action("s", sell_idx=sell_idx)
            elif action == 12:
                # Trade - use same logic as env
                trade_in, trade_out = env._find_valid_trade(state)
                if trade_in and trade_out:
                    success = game_engine.do_action("t", trade_in=trade_in, trade_out=trade_out)

            if not success:
                # Fall back to random valid action
                print("(RL agent chose invalid action, falling back to random)")
                from RandomPlayer import RandomPlayer
                fallback = RandomPlayer(game_engine)
                fallback.take_action()

    game_engine.get_scores()


def main():
    parser = argparse.ArgumentParser(description="Train or evaluate Jaipur RL agent")
    parser.add_argument("--timesteps", type=int, default=100000,
                        help="Number of training timesteps (default: 100000)")
    parser.add_argument("--envs", type=int, default=4,
                        help="Number of parallel environments (default: 4)")
    parser.add_argument("--eval", action="store_true",
                        help="Evaluate a trained model")
    parser.add_argument("--play", action="store_true",
                        help="Play against trained model")
    parser.add_argument("--model", type=str, default=None,
                        help="Path to model file (for --eval or --play)")
    parser.add_argument("--episodes", type=int, default=200,
                        help="Number of evaluation episodes (default: 200)")

    args = parser.parse_args()

    if args.eval:
        if not args.model:
            # Find most recent model
            models_dir = "models"
            if os.path.exists(models_dir):
                models = [f for f in os.listdir(models_dir) if f.startswith("jaipur_ppo")]
                if models:
                    args.model = os.path.join(models_dir, sorted(models)[-1])

        if not args.model or not os.path.exists(args.model + ".zip"):
            print("No model found. Train one first with: python train.py")
            return

        evaluate(args.model, args.episodes)

    elif args.play:
        if not args.model:
            models_dir = "models"
            if os.path.exists(models_dir):
                models = [f for f in os.listdir(models_dir) if f.startswith("jaipur_ppo")]
                if models:
                    args.model = os.path.join(models_dir, sorted(models)[-1])

        if not args.model or not os.path.exists(args.model + ".zip"):
            print("No model found. Train one first with: python train.py")
            return

        play_against_model(args.model)

    else:
        train(timesteps=args.timesteps, n_envs=args.envs)


if __name__ == "__main__":
    main()
