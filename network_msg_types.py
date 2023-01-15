import pickle

class LobbyPlayerStatus():
    def __init__(self, name):
        self.name = name

class LobbyStatus():
    def __init__(self):
        self.players_list = []
        self.start_game = False
        
    def add_player(self, name):
        self.players_list.append(name)
        
    def remove_player(self, name):
        self.players_list.remove(name)
        
print(len(pickle.dumps(LobbyStatus())))
