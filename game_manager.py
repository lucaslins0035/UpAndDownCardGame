from dealer import Dealer
from namings import *
from collections import deque


class GameManager():
    def __init__(self, players_list):
        self.dealer = Dealer()
        self.dealer.deck.shuffle()

        self.game_state = BETTING
        self.num_players = len(players_list)
        self.rounds = 52//self.num_players
        self.game_phase = "up"
        self.init_player_index = -1  # The index of the players_list inside the game_status

        self.current_round = 0
        self.current_hands = {name: None for name in players_list}
        self.current_wild_card = None
        self.current_playing_order = deque(range(self.num_players))
        # The list will rotate -1 in the beginning of every betting phase
        self.current_playing_order.rotate(1)
        self.current_playing_index = -1

    def get_next_round(self):
        if self.current_round < self.rounds and self.game_phase == "up":
            self.current_round = self.current_round+1
        elif self.current_round == self.rounds and self.game_phase == "up":
            self.current_round = self.current_round - 1
            self.game_phase = "down"
        elif self.current_round < self.rounds and self.game_phase == "down":
            self.current_round = self.current_round - 1
        else:
            raise ValueError(
                "Current round value must be positive integer <= rounds")

    def get_next_init_player_index(self):
        self.current_playing_order.rotate(-1)
        self.init_player_index = self.current_playing_order[0]

    def setup_next_round(self):
        self.get_next_round()
        self.get_next_init_player_index()
        current_hands, self.current_wild_card = self.dealer.deal_cards(
            self.num_players, self.current_round)

        for i, name in enumerate(self.current_hands.keys()):
            self.current_hands[name] = current_hands[i]

        self.current_playing_index = self.init_player_index

    # Pass turn to the next player
    def pass_turn(self):
        try:
            self.current_playing_index = self.current_playing_order[
                self.current_playing_order.index(
                    self.current_playing_index) + 1]
        except:
            self.current_playing_index = None
