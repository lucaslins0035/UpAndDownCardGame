import threading

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import StringProperty, Clock, ListProperty

from gameServer import GameServer
from gameclient import GameClient
from namings import *

game_server = GameServer('127.0.0.1', 7777)
game_client = GameClient('127.0.0.1', 7777)


class PlayMenu(Screen):
    warning_text = StringProperty("")

    def on_create_room(self, name_input):
        global game_server
        game_server = GameServer('127.0.0.1', 7777)

        global game_client
        game_client = GameClient('127.0.0.1', 7777)
        game_client.type = HOST

        # TODO make them daemon threads?
        global server_thread
        server_thread = threading.Thread(target=game_server.run, daemon=True)

        global client_thread
        client_thread = threading.Thread(target=game_client.run, daemon=True)

        if name_input.text == "":
            self.warning_text = "Please provide a name"
        else:
            print("My name is ", name_input.text)

            server_thread.start()
            server_thread.join(0.2)

            if server_thread.is_alive():
                game_client.set_name(name_input.text)
                client_thread.start()
                move_through_lobby(self, 'in')
                #self.manager.current = 'lobby'
            else:
                self.warning_text = "Address already in use"

    def on_enter_room(self, name_input):
        global game_client
        game_client = GameClient('127.0.0.1', 7777)
        game_client.type = CLIENT

        global client_thread
        client_thread = threading.Thread(target=game_client.run, daemon=True)

        if name_input.text == "":
            self.warning_text = "Please provide a name"
        else:
            print("My name is ", name_input.text)

            game_client.set_name(name_input.text)
            client_thread.start()
            client_thread.join(0.2)

            if client_thread.is_alive():
                move_through_lobby(self, 'in')
                #self.manager.current = 'lobby'
            else:
                self.warning_text = "There is no server running with this address"


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

        leave_btn = Button(text='Leave',
                           size_hint=(0.6, 1))
        leave_btn.bind(on_release=self.on_leave_btn)

        play_btn = Button(text='Play',
                          size_hint=(0.6, 1))

        btns_box.add_widget(leave_btn)
        btns_box.add_widget(play_btn)

        box_background.add_widget(title)
        box_background.add_widget(players_grid)
        box_background.add_widget(btns_box)

        self.add_widget(box_background)

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
        move_through_lobby(self, 'out')
        self.manager.current = 'play_menu'


class UpAndDownApp(App):
    def build(self):
        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(PlayMenu(name="play_menu"))
        sm.add_widget(Lobby(name="lobby"))
        return sm


def move_through_lobby(screen, action):
    global check_server_life_event
    if action == "in":
        check_server_life_event = Clock.schedule_interval(
            lambda dt: check_server_life(screen), 1)
        screen.manager.current = 'lobby'
    elif action == 'out':
        check_server_life_event.cancel()


def check_server_life(screen):
    global server_thread
    global client_thread

    client_thread.join(0.1)

    if not client_thread.is_alive() and screen.manager.current == 'lobby':
        game_client.close_client = True
        client_thread.join()
        move_through_lobby(screen, 'out')
        screen.manager.current = 'play_menu'


# Main
try:
    UpAndDownApp().run()
except:
    if server_thread.is_alive():
        game_server.close_server = True
        server_thread.join()
    if client_thread.is_alive():
        game_client.close_client = True
        client_thread.join()
