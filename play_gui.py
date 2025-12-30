#!/usr/bin/env python3
"""
Play Jaipur with a graphical interface.
Human player (GUI) vs RandomPlayer AI.
"""
import sys
from GameEngine import GameEngine
from GUIPlayer import GUIPlayer
from RandomPlayer import RandomPlayer


def main():
    # Suppress console output from game engine during GUI play
    class QuietGameEngine(GameEngine):
        def __init__(self):
            # Temporarily redirect print during init
            import builtins
            original_print = builtins.print
            builtins.print = lambda *args, **kwargs: None
            super().__init__()
            builtins.print = original_print

    print("Starting Jaipur GUI...")
    print("You are Player 1 (bottom). AI is Player 2 (top).")
    print()

    game_engine = QuietGameEngine()

    # Human player is always player 0, AI is player 1
    gui_player = GUIPlayer(game_engine)
    ai_player = RandomPlayer(game_engine)
    players = [gui_player, ai_player]

    # Suppress prints during gameplay
    import builtins
    original_print = builtins.print

    while not game_engine.is_done():
        current_player = game_engine.whos_turn

        if current_player == 0:
            # Human's turn - show GUI
            builtins.print = original_print  # Restore for debugging
            builtins.print = lambda *args, **kwargs: None  # Then suppress
            players[0].take_action()
        else:
            # AI's turn
            builtins.print = lambda *args, **kwargs: None
            players[1].take_action()

    # Game over - get scores
    builtins.print = lambda *args, **kwargs: None
    scores, winner = game_engine.get_scores()
    builtins.print = original_print

    # Adjust winner index since human is always player 0
    # But game engine assigns player indices based on who went first
    # So we need to figure out which player index the GUI player has

    # Show game over screen
    gui_player.show_game_over(scores, winner)

    print()
    print("=" * 40)
    print("GAME OVER")
    print(f"Your Score: {scores[0]}")
    print(f"AI Score: {scores[1]}")
    if winner == 0:
        print("YOU WIN!")
    elif winner == 1:
        print("AI WINS!")
    else:
        print("IT'S A TIE!")
    print("=" * 40)


if __name__ == "__main__":
    main()
