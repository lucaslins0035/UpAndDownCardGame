import threading

mobile_screen_ration = 19.5/9
from kivy.config import Config
Config.set('graphics', 'width', '498')
Config.set('graphics', 'height', '1080')

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDTextButton
from kivy.metrics import dp
from kivy.properties import StringProperty, Clock


from gameServer import GameServer
from gameclient import GameClient
from namings import *

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
        box_background = MDBoxLayout(orientation='vertical')

        players_grid = MDGridLayout(rows=5)

        # Lobby list
        title = MDLabel(text="Players",
                        font_size=30,
                        halign="center",
                        valign="center",
                        size_hint=(1, None),
                        size=(dp(100), dp(80)))
        title.text_size = title.size

        self.players_list = []
        for i in range(10):
            self.players_list.append(
                MDLabel(text="{}: ***********".format("H" if i == 0 else str(i+1)),
                        font_size=20)
            )
            players_grid.add_widget(self.players_list[-1])

        btns_box = MDBoxLayout(orientation="horizontal",
                               size_hint=(1, None), size=(dp(0), dp(60)),
                               spacing=dp(25),
                               padding=dp(25))

        self.leave_btn = MDTextButton(text='Leave',
                                      size_hint=(0.6, 1))
        self.leave_btn.bind(on_release=self.on_leave_btn)

        self.play_btn = MDTextButton(text='Play',
                                     size_hint=(0.6, 1))

        btns_box.add_widget(self.leave_btn)
        btns_box.add_widget(self.play_btn)

        box_background.add_widget(title)
        box_background.add_widget(players_grid)
        box_background.add_widget(btns_box)

        self.add_widget(box_background)

    def on_pre_enter(self, *args):
        global game_client

        super().on_pre_enter(*args)
        Clock.schedule_once(lambda dt: self.update_lobby_list(), -1)

        if game_client.type != HOST:
            self.play_btn.disabled = True
        else:
            self.play_btn.disabled = False

    def on_enter(self, *args):
        super().on_enter(*args)
        self.check_server_life_event = Clock.schedule_interval(
            lambda dt: self.check_server_life(), 1)
        self.update_lobby_list_event = Clock.schedule_interval(
            lambda dt: self.update_lobby_list(), 1)

    def on_leave(self, *args):
        super().on_leave(*args)
        self.check_server_life_event.cancel()
        self.update_lobby_list_event.cancel()

    def check_server_life(self):
        global server_thread
        global client_thread
        print("Check server")

        client_thread.join(0.1)

        if not client_thread.is_alive() and self.manager.current == 'lobby':
            game_client.close_client = True
            client_thread.join()
            self.manager.current = 'play_menu'

    def on_leave_btn(self, instance):
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

    def update_lobby_list(self):
        global game_client

        num_players = len(game_client.lobby_status.players_list)
        for i in range(num_players):
            self.players_list[i].text = "{}: {}".format(
                "H" if i == 0 else str(i+1), game_client.lobby_status.players_list[i])

        for i in range(num_players, len(self.players_list)):
            self.players_list[i].text = "{}: {}".format(
                "H" if i == 0 else str(i+1), "")


class UpAndDownApp(MDApp):
    def build(self):
        # Create the screen manager
        sm = MDScreenManager()
        sm.add_widget(PlayMenu(name="play_menu"))
        sm.add_widget(Lobby(name="lobby"))
        return sm


# Main
# try:
UpAndDownApp().run()
# except:
#     if server_thread.is_alive():
#         game_server.close_server = True
#         server_thread.join()
#     if client_thread.is_alive():
#         game_client.close_client = True
#         client_thread.join()
