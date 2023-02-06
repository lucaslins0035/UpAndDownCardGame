from collections import deque
import pydealer as pd

from dealer import Dealer
from namings import *


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
        self.round_count = 0
        self.current_hands = {name: None for name in players_list}
        self.current_wild_card = None
        self.current_playing_order = deque(range(self.num_players))
        # The list will rotate -1 in the beginning of every betting phase
        self.current_playing_order.rotate(1)
        self.current_playing_index = None

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
        if self.current_round == 0:
            return

        self.get_next_init_player_index()
        current_hands, self.current_wild_card = self.dealer.deal_cards(
            self.num_players, self.current_round)

        for i, name in enumerate(self.current_hands.keys()):
            self.current_hands[name] = current_hands[i]

        self.current_playing_index = self.init_player_index
        self.round_count = 1

    def finish_round(self):
        if self.round_count < self.current_round:
            self.round_count = self.round_count + 1
            return False
        return True

    def pass_turn(self):  # Pass turn to the next player
        # Restart counting turns
        if self.current_playing_index is None:
            self.current_playing_index = self.init_player_index
            return

        # Passing turns
        try:
            self.current_playing_index = self.current_playing_order[
                self.current_playing_order.index(
                    self.current_playing_index) + 1]
        except:
            # After everyone played
            self.current_playing_index = None

    def get_partial_winner(self, cards_dict):
        cards = pd.Stack(cards=cards_dict.values())
        max_card = self.dealer.get_max_card(cards)

        for name in cards_dict.keys():
            if cards_dict[name] == max_card:
                return name
