#!/usr/bin/env python3
"""
Play Jaipur with a graphical interface.
Human player (GUI) vs RL-trained AI (or RandomPlayer as fallback).
"""
import sys
import builtins
from GameEngine import GameEngine
from GUIPlayer import GUIPlayer
from RLPlayer import RLPlayer


def play_game(gui_player=None):
    """Play a single game. Returns (gui_player, play_again)."""
    # Suppress console output from game engine during GUI play
    original_print = builtins.print
    builtins.print = lambda *args, **kwargs: None

    game_engine = GameEngine()

    builtins.print = original_print

    # Create or reset GUI player
    if gui_player is None:
        gui_player = GUIPlayer(game_engine)
    else:
        # Reset for new game
        gui_player.game_engine = game_engine
        gui_player._my_player_index = None
        gui_player._selected_hand = []
        gui_player._selected_market = []

    ai_player = RLPlayer(game_engine)
    players = [gui_player, ai_player]

    # Suppress prints during gameplay
    builtins.print = lambda *args, **kwargs: None

    while not game_engine.is_done():
        current_player = game_engine.whos_turn

        if current_player == gui_player._my_player_index or gui_player._my_player_index is None:
            # Human's turn
            players[0].take_action()
        else:
            # AI's turn
            players[1].take_action()

    # Game over - get scores
    scores, winner = game_engine.get_scores()
    builtins.print = original_print

    # Show game over screen and get choice
    play_again = gui_player.show_game_over(scores, winner)

    return gui_player, play_again


def main():
    print("Starting Jaipur GUI...")
    print("You play against the RL-trained AI.")
    print()

    gui_player = None
    play_again = True

    while play_again:
        gui_player, play_again = play_game(gui_player)

    print("Thanks for playing!")


if __name__ == "__main__":
    main()
