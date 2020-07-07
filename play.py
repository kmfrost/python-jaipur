from GameEngine import GameEngine
from Player import Player
from RandomPlayer import RandomPlayer

def main():
    game_engine = GameEngine()
    players = [Player(game_engine), RandomPlayer(game_engine)]
    while not game_engine.is_done():
        players[game_engine.whos_turn].take_action()
    game_engine.get_scores()

if __name__ == "__main__":
    main()