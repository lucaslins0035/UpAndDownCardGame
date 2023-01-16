import threading

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import StringProperty

from gameServer import GameServer
from gameclient import GameClient

game_server = GameServer('127.0.0.1', 7777)
game_client = GameClient('127.0.0.1', 7777)
# TODO make them daemon threads?
server_thread = threading.Thread(target=game_server.run)
client_thread = threading.Thread(target=game_client.run)


class PlayMenu(Screen):
    warning_text = StringProperty("")

    def on_create_room(self, name_input):
        if name_input.text == "":
            self.warning_text = "Please provide a name"
        else:
            print("My name is ", name_input.text)
            server_thread.start()

            game_client.set_name(name_input.text)
            client_thread.start()

            self.manager.current = 'lobby'

    def on_enter_room(self, name_input):
        if name_input.text == "":
            self.warning_text = "Please provide a name"
        else:
            print("My name is ", name_input.text)

            game_client.set_name(name_input.text)
            client_thread.start()

            self.manager.current = 'lobby'


class Lobby(Screen):
    # Create graphics
    def __init__(self, **kw):
        super().__init__(**kw)
        box_background = BoxLayout(orientation='vertical')

        players_grid = GridLayout(rows=5)

        # Lobby list
        title = Label(text="Players",
                      font_size=30,
                      halign="center",
                      valign="center",
                      size_hint=(1, None),
                      size=(dp(100), dp(80)))
        title.text_size = title.size

        self.players_list = []
        for i in range(10):
            self.players_list.append(
                Label(text="{}: ***********".format("H" if i == 0 else str(i+1)),
                      font_size=20)
            )
            players_grid.add_widget(self.players_list[-1])

        btns_box = BoxLayout(orientation="horizontal",
                             size_hint=(1, None), size=(dp(0), dp(60)),
                             spacing=dp(25))
        btns_box.add_widget(Button(text='Leave', size_hint=(0.6, 1)))
        btns_box.add_widget(Button(text='Play', size_hint=(0.6, 1)))

        box_background.add_widget(title)
        box_background.add_widget(players_grid)
        box_background.add_widget(btns_box)

        self.add_widget(box_background)
        
        def update_players_list(self):
            pass


class UpAndDownApp(App):
    def build(self):
        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(PlayMenu(name="play_menu"))
        sm.add_widget(Lobby(name="lobby"))
        return sm


try:
    UpAndDownApp().run()
except:
    if server_thread.is_alive():
        game_server.close_server = True
        server_thread.join()
    if client_thread.is_alive():
        game_client.close_client = True
        client_thread.join()
