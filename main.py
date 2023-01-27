import threading
from functools import partial

from kivy.config import Config  # noqa
Config.set('graphics', 'width', '498')  # noqa
Config.set('graphics', 'height', '1080')  # noqa

from kivy.properties import StringProperty, Clock, NumericProperty
from kivy.metrics import dp
from kivymd.uix.button import MDTextButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivy.uix.label import Label
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivy.uix.popup import Popup
from kivymd.app import MDApp

from gameServer import GameServer
from namings import *
from gameclient import GameClient

game_server = GameServer('127.0.0.1', 7777)
game_client = GameClient('127.0.0.1', 7777)


class PlayMenu(MDScreen):
    warning_text = StringProperty("")

    def on_create_room(self):
        if self.ids.name_input.text == "" or self.ids.name_input.error:
            self.ids.name_input.error = True
        elif self.ids.ip_input.text == "":
            self.ids.ip_input.error = True
        elif self.ids.port_input.text == "":
            self.ids.port_input.error = True
        else:
            global game_server
            game_server = GameServer(
                self.ids.ip_input.text, int(self.ids.port_input.text))

            global game_client
            game_client = GameClient(
                self.ids.ip_input.text, int(self.ids.port_input.text))
            game_client.type = HOST

            global server_thread
            server_thread = threading.Thread(
                target=game_server.run, daemon=True)

            global client_thread
            client_thread = threading.Thread(
                target=game_client.run, daemon=True)

            server_thread.start()
            server_thread.join(0.2)

            if server_thread.is_alive():
                game_client.set_name(self.ids.name_input.text)
                client_thread.start()
                self.manager.current = 'lobby'
            else:
                self.warning_text = "Address already in use"

    def on_enter_room(self):
        if self.ids.name_input.text == "" or self.ids.name_input.error:
            self.ids.name_input.error = True
        elif self.ids.ip_input.text == "":
            self.ids.ip_input.error = True
        elif self.ids.port_input.text == "":
            self.ids.port_input.error = True
        else:
            global game_client
            game_client = GameClient(
                self.ids.ip_input.text, int(self.ids.port_input.text))
            game_client.type = CLIENT

            global client_thread
            client_thread = threading.Thread(
                target=game_client.run, daemon=True)

            game_client.set_name(self.ids.name_input.text)
            client_thread.start()
            client_thread.join(0.2)

            if client_thread.is_alive():
                self.manager.current = 'lobby'
            else:
                self.warning_text = "There is no server running with this address"


class Lobby(MDScreen):
    # Create graphics

    def __init__(self, **kw):
        super().__init__(**kw)

        # Create list of players
        self.players_list = []
        for i in range(10):
            self.players_list.append(
                Label(text=self.write_list_name(i, ". . ."),
                      font_size=50,
                      halign="center",
                      valign="center",
                      font_name="fonts/refik/RefikBook.ttf",
                      outline_color=(0, 0, 0),
                      outline_width=3,
                      size_hint=(1, None),
                      size=(1, dp(60)),
                      )
            )
            self.ids.players_grid.add_widget(self.players_list[-1])

    def write_list_name(self, i, name):
        return "{} .   {}".format(
            "H" if i == 0 else str(i+1),
            name)

    def on_pre_enter(self, *args):
        global game_client

        super().on_pre_enter(*args)
        Clock.schedule_once(lambda dt: self.update_lobby(), -1)

        if game_client.type != HOST:
            self.ids.play_btn.disabled = True
        else:
            self.ids.play_btn.disabled = False

    def on_enter(self, *args):
        super().on_enter(*args)
        self.check_server_life_event = Clock.schedule_interval(
            lambda dt: check_server_life(self), 1)
        self.update_lobby_event = Clock.schedule_interval(
            lambda dt: self.update_lobby(), 1)

    def on_leave(self, *args):
        super().on_leave(*args)
        self.check_server_life_event.cancel()
        self.update_lobby_event.cancel()


    def on_leave_btn(self):
        global game_client
        global game_server
        global server_thread
        global client_thread
        if game_client.type == HOST:
            game_server.close_server = True
            game_client.close_client = True
            server_thread.join()
            client_thread.join()
        else:
            game_client.close_client = True
            client_thread.join()
        self.manager.current = 'play_menu'

    def on_play_btn(self):
        game_client.player_status.start_game = True

    def update_lobby(self):
        global game_client

        # Update lobby list
        num_players = len(game_client.game_status.players_list)
        for i in range(num_players):
            self.players_list[i].text = self.write_list_name(
                i, game_client.game_status.players_list[i])

        for i in range(num_players, len(self.players_list)):
            self.players_list[i].text = self.write_list_name(i, ". . .")

        # Check start game
        if game_client.game_state == GAME:
            # print(game_client.game_state)
            self.manager.current = 'game_play'

def check_server_life(screen):
    global server_thread
    global client_thread
    print("Check server")

    client_thread.join(0.1)

    if not client_thread.is_alive() and screen.manager.current in ['lobby', 'game_play']:
        game_client.close_client = True
        client_thread.join()
        screen.manager.current = 'play_menu'

class GamePlay(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exit_popup = ExitGamePopup()
        self.exit_popup.ids['exit_btn'].bind(on_release=self.on_exit_btn_popup)

    def on_pre_enter(self, *args):
        global game_client
        super().on_pre_enter(*args)
        num_players = len(game_client.game_status.players_list)

        # Write player names
        for i in range(num_players):
            self.ids["player" +
                     str(i+1)].name = game_client.game_status.players_list[i]
        for i in range(num_players, 10):
            self.ids["player" +
                     str(i+1)].name = ""

    def on_enter(self, *args):
        super().on_enter(*args)
        self.check_server_life_event = Clock.schedule_interval(
            lambda dt: check_server_life(self), 1)

    def on_exit_btn(self):
        self.exit_popup.open()

    def on_exit_btn_popup(self, instance):
        global game_client
        global game_server
        global server_thread
        global client_thread
        if game_client.type == HOST:
            game_server.close_server = True
            game_client.close_client = True
            server_thread.join()
            client_thread.join()
        else:
            game_client.close_client = True
            client_thread.join()
        self.exit_popup.dismiss()
        self.manager.current = 'play_menu'
            
    def on_leave(self, *args):
        super().on_leave(*args)
        self.check_server_life_event.cancel()


class ExitGamePopup(Popup):
    pass


class PlayerSpot(MDBoxLayout):
    name = StringProperty("Player")
    bet = NumericProperty(0)
    current_score = NumericProperty(0)
    card = StringProperty("images/empty_card.png")
    # TODO method change card


class UpAndDownApp(MDApp):
    def build(self):
        # Create the screen manager
        sm = MDScreenManager()
        sm.add_widget(PlayMenu(name="play_menu"))
        sm.add_widget(Lobby(name="lobby"))
        sm.add_widget(GamePlay(name="game_play"))
        return sm


UpAndDownApp().run()
