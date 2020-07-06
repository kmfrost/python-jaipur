from GameEngine import GameEngine
from Player import Player

def main():
    game_engine = GameEngine()
    players = [Player(game_engine), Player(game_engine)]
    while not game_engine.is_done():
        players[game_engine.whos_turn].take_action()

if __name__ == "__main__":
    main()