class LobbyPlayerStatus():
    def __init__(self):
        self.name = ""


class LobbyStatus():
    def __init__(self):
        self.players_reg = {}
        self.players_list = []
        self.start_game = False

    def _update_list(self):
        self.players_list = [name for name in self.players_reg.values()]

    def add_player(self, player_name, addr):
        self.players_reg.update({addr: player_name})
        self._update_list()

    def remove_player(self, addr):
        self.players_reg.pop(addr)
        self._update_list()
