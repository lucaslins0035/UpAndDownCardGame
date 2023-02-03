from namings import *
from pydealer.stack import Stack


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
        self.current_hand = Stack()
        self.init_player_index = -1
        self.playing_order = []
        self.state = LOBBY

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
                                            'current_hand': Stack()}})
        self.round_num = 1
        self.state = BETTING
        self.screen = "betting"
        self.current_wild_card = None

    def update_player_data(self, hands, current_player, playing_order):
        for player in self.players_list:
            if self.players_list[current_player] == player:
                self.player_data[player]["playing"] = True
            else:
                self.player_data[player]["playing"] = False

        for name, hand in hands.items():
            self.player_data[name]['current_hand'] = hand

        self.playing_order = playing_order
