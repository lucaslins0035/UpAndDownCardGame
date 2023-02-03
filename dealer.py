from pydealer.deck import Deck
from pydealer.stack import Stack


class Dealer():
    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()

        # Up and down card rank
        self.UD_RANK = {
            "values": {
                "Ace": 13,
                "King": 12,
                "Queen": 11,
                "Jack": 10,
                "10": 9,
                "9": 8,
                "8": 7,
                "7": 6,
                "6": 5,
                "5": 4,
                "4": 3,
                "3": 2,
                "2": 1,
                "Joker": 0
            },
            "suits": {
                "Spades": 4,
                "Hearts": 3,
                "Clubs": 2,
                "Diamonds": 1
            }
        }

    def update_card_rank(self, init, wild):
        aux = 2
        for suit in self.UD_RANK['suits'].keys():
            if suit == wild:
                self.UD_RANK['suits'][suit] = 4
            elif suit == init:
                self.UD_RANK['suits'][suit] = 3
            else:
                self.UD_RANK['suits'][suit] = aux
                aux = aux-1

    def gt(self, card_a, card_b):
        if self.UD_RANK['suits'][card_a.suit] > self.UD_RANK['suits'][card_b.suit]:
            return True
        elif self.UD_RANK['suits'][card_a.suit] == self.UD_RANK['suits'][card_b.suit]:
            if self.UD_RANK['values'][card_a.value] > self.UD_RANK['values'][card_b.value]:
                return True
            else:
                return False
        else:
            return False

    def get_max_card(self, stack):
        return self.sort_cards(stack)[0]

    def sort_cards(self, cards):
        if self.UD_RANK.get("values"):
            cards = sorted(
                cards,
                key=lambda x: self.UD_RANK["values"][x.value],
                reverse=True
            )
        if self.UD_RANK.get("suits"):
            cards = sorted(
                cards,
                key=lambda x: self.UD_RANK["suits"][x.suit],
                reverse=True
            )

        return Stack(list=cards)
    
    def deal_cards(self, num_players, round):
        if len(self.deck) != 52:
            raise ValueError("Deck must be full to redistribute")

        self.deck.shuffle()
        
        hands = [Stack() for _ in range(num_players)]
        
        for _ in range(round):
            for p in range(num_players):
                hands[p].add(self.deck.deal(1))
                
        self.wild_card = self.deck.deal(1)
                
        return tuple(hands), self.deck.deal(1)
