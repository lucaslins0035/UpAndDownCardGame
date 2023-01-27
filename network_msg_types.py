class LobbyPlayerStatus():
    def __init__(self):
        self.name = ""
        self.start_game = False


class LobbyStatus():
    def __init__(self):
        self.players_list = []
        self.start_game = False

    def update_list(self, reg):
        self.players_list = [name for name in reg.values()]
