from namings import *

class PlayerStatus():
    def __init__(self):
        self.name = ""
        self.start_game = False
        self.current_bet = None
        self.card_played = None
        self.playing = False


class GameStatus():
    def __init__(self):
        self.valid_game = False
        self.players_list = []

    def update_list(self, reg):
        self.players_list = [name for name in reg.values()]

    def init_game_data(self):
        self.player_data = {}
        for name in self.players_list:
            self.player_data.update({name: {'total_score': 0,
                                            'current_score': 0,
                                            'current_bet': None,
                                            'card_played': None,
                                            'playing': False,
                                            'init_player': False}})
        self.round_num = 1
        self.state = BETTING
        self.screen = "betting"
