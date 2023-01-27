class PlayerStatus():
    def __init__(self):
        self.name = ""
        self.start_game = False


class GameStatus():
    def __init__(self):
        self.valid_game = False
        self.players_list = []

    def update_list(self, reg):
        self.players_list = [name for name in reg.values()]
