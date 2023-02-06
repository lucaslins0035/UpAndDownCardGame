import threading
from functools import partial

from kivy.config import Config  # noqa
Config.set('graphics', 'width', '498')  # noqa
Config.set('graphics', 'height', '1080')  # noqa

from kivy.properties import StringProperty, Clock, NumericProperty, ListProperty, ObjectProperty
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem
from kivymd.uix .card import MDCard

from gameServer import GameServer
from namings import *
from gameclient import GameClient

game_server = GameServer('127.0.0.1', 7777)
game_client = GameClient('127.0.0.1', 7777)

########################################################################
#   SCREENS
########################################################################


class PlayMenu(MDScreen):
    warning_text = StringProperty("")

    def on_create_room(self):
        # TODO revert every commit
        # if self.ids.name_input.text == "" or self.ids.name_input.error:
        #     self.ids.name_input.error = True
        # elif self.ids.ip_input.text == "":
        #     self.ids.ip_input.error = True
        # elif self.ids.port_input.text == "":
        #     self.ids.port_input.error = True
        # else:

        self.ids.name_input.text = "Lucas"
        self.ids.ip_input.text = "127.0.0.1"
        self.ids.port_input.text = "7777"

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
        # if self.ids.name_input.text == "" or self.ids.name_input.error:
        #     self.ids.name_input.error = True
        # elif self.ids.ip_input.text == "":
        #     self.ids.ip_input.error = True
        # elif self.ids.port_input.text == "":
        #     self.ids.port_input.error = True
        # else:

        import names
        self.ids.name_input.text = names.get_first_name()
        self.ids.ip_input.text = "127.0.0.1"
        self.ids.port_input.text = "7777"

        global game_client
        game_client = GameClient(
            self.ids.ip_input.text, int(self.ids.port_input.text))
        game_client.type = CLIENT

        game_client.set_name(self.ids.name_input.text)

        global client_thread
        client_thread = threading.Thread(
            target=game_client.run, daemon=True)

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
                      font_size=40,
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
        if game_client.game_status.state != LOBBY:
            self.manager.current = game_client.game_status.screen


class GamePlay(MDScreen):
    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.ids.top_win_menu.set_menu()
        self.ids.table.update_table_view()
        self.ids.player_hand.setup_player_hand()

        self.ids.table.wild_card_src = get_card_img_path(
            game_client.game_status.current_wild_card)

    def on_enter(self, *args):
        super().on_enter(*args)
        self.check_server_life_event = Clock.schedule_interval(
            lambda dt: check_server_life(self), 1)
        self.update_gameplay_screen_event = Clock.schedule_interval(
            lambda dt: self.update_gameplay_screen(), 0.2)

    def on_leave(self, *args):
        super().on_leave(*args)
        self.check_server_life_event.cancel()
        self.update_gameplay_screen_event.cancel()

    def update_gameplay_screen(self):
        global game_client

        self.ids.table.update_table_view()
        self.ids.player_hand.setup_player_hand()

        # Check start round
        if game_client.game_status.state != PLAYING:
            self.manager.current = game_client.game_status.screen


class Betting(MDScreen):
    drop_down = DropDown()
    current_round = NumericProperty(0)

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        # Setup sub screens
        self.ids.top_win_menu.set_menu()
        self.ids.player_hand.setup_player_hand()

        global game_client

        self.current_round = game_client.game_status.round_num

        # Create betting list
        self.ids.betting_list.clear_widgets()
        for i in game_client.game_status.playing_order:
            list_item = OneLineListItem(id=game_client.game_status.players_list[i],
                                        text=game_client.game_status.players_list[i] + ": ...")
            self.ids.betting_list.add_widget(list_item)
            self.ids.update(
                {game_client.game_status.players_list[i]: list_item})

        # Create drop down betting menu
        self.drop_down.clear_widgets()
        for i in range(game_client.game_status.round_num + 1):
            btn = Button(text="{}".format(i), size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.drop_down.select(int(btn.text)))
            self.drop_down.add_widget(btn)

        self.ids.drop_down_btn.text = "Choose your bet"
        self.ids.drop_down_btn.bind(on_release=self.drop_down.open)
        self.drop_down.bind(on_select=lambda instance, x: setattr(
            self.ids.drop_down_btn, "text", str(x)))
        self.ids.confirm_btn.bind(on_release=self.on_confirm_btn)

        self.ids.wild_card_img.source = get_card_img_path(
            game_client.game_status.current_wild_card)

    def on_enter(self, *args):
        super().on_enter(*args)

        # Initiate events
        self.check_server_life_event = Clock.schedule_interval(
            lambda dt: check_server_life(self), 1)
        self.update_betting_screen_event = Clock.schedule_interval(
            lambda dt: self.update_betting_screen(), 0.2)

    def on_leave(self, *args):
        super().on_leave(*args)
        self.check_server_life_event.cancel()
        self.update_betting_screen_event.cancel()

    def on_confirm_btn(self, instance):
        print("Writing current bet")
        game_client.player_status.current_bet = int(
            self.ids.drop_down_btn.text)

    def update_betting_screen(self):
        # Update betting list
        for player_index in game_client.game_status.playing_order:
            name = game_client.game_status.players_list[player_index]
            current_bet = game_client.game_status.player_data[name]["current_bet"]
            bet_str = str(current_bet) if current_bet is not None else "..."
            self.ids[name].text = name + \
                ": " + bet_str

            if game_client.game_status.player_data[name]['playing']:
                self.ids[name].bg_color = (1, 1, 1, 1)
            else:
                self.ids[name].bg_color = (1, 1, 1, 0)

        # Update button status
        if game_client.game_status.player_data[game_client.name]['playing'] and game_client.player_status.current_bet is None:
            self.ids.drop_down_btn.disabled = False

            # Allow confirming bet only after choosing a valid one
            if self.ids.drop_down_btn.text != "Choose your bet":
                self.ids.confirm_btn.disabled = False
        else:
            self.ids.drop_down_btn.disabled = True
            self.ids.confirm_btn.disabled = True

        # Check start round
        if game_client.game_status.state != BETTING:
            self.manager.current = game_client.game_status.screen


########################################################################
#   PARTS OF SCREENS
########################################################################


class ExitGamePopup(Popup):
    pass


class Table(MDAnchorLayout):
    wild_card_src = StringProperty("images/empty_card.png")

    def on_wild_card_src(self, instance, value):
        self.ids.wild_card_img.source = value

    def update_table_view(self):
        global game_client
        num_players = len(game_client.game_status.players_list)

        self.ids.suit.text = "[b]SUIT: {}[/b]".format(
            game_client.game_status.current_round_suit)

        # Write player names
        for i in range(num_players):
            name = game_client.game_status.players_list[i]
            self.ids["player" +
                     str(i+1)].name = name
            curr_bet = game_client.game_status.player_data[name]['current_bet']
            self.ids["player" +
                     str(i+1)].bet = curr_bet if curr_bet is not None else -1
            self.ids["player" +
                     str(i+1)].current_score = game_client.game_status.player_data[name]['current_score']
            self.ids["player" +
                     str(i+1)].total_score = game_client.game_status.player_data[name]['total_score']
            self.ids["player" +
                     str(i+1)].card = get_card_img_path(game_client.game_status.player_data[name]['card_played'])

        for i in range(num_players, 10):
            self.ids["player" +
                     str(i+1)].name = "..."


class TopWindowMenu(MDRelativeLayout):
    def set_menu(self):
        self.exit_popup = ExitGamePopup()
        self.exit_popup.ids['exit_btn'].bind(on_release=self.on_exit_btn_popup)
        self.ids['quit_btn'].bind(on_release=self.on_exit_btn)

    def on_exit_btn(self, intance):
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


class PlayingCard(MDCard):

    card = ObjectProperty(None)
    pressed = ListProperty([0, 0])
    double_pressed = ListProperty([0, 0])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                self.double_pressed = touch.pos
            else:
                self.pressed = touch.pos

            return True
        return super(PlayingCard, self).on_touch_down(touch)

    def on_pressed(self, instance, pos):
        global game_client
        if game_client.game_status.player_data[game_client.name]['playing'] and \
                game_client.player_status.card_played is None and \
                game_client.game_status.state == PLAYING:

            if self.check_valid_card(instance.card.suit):
                game_client.player_status.card_played = instance.card
            else:
                print("Please play {}".format(
                    game_client.game_status.current_round_suit))

    def on_double_pressed(self, instance, pos):
        print('on_double_pressed at {pos}'.format(pos=pos))

    def check_valid_card(self, played_suit):
        if game_client.game_status.current_round_suit is None:
            return True
        elif played_suit == game_client.game_status.current_round_suit:
            return True
        elif not any(card.suit == game_client.game_status.current_round_suit
                 for card in game_client.game_status.player_data[game_client.name]['current_hand']):
            return True
        
        return False


class PlayerHand(MDScrollView):
    def setup_player_hand(self):
        self.ids.box_layout.clear_widgets()
        width = 0
        for card in game_client.game_status.player_data[game_client.name]["current_hand"]:
            md_card_anchorl = MDAnchorLayout()
            card_img = Image(source=get_card_img_path(card))
            md_card_anchorl.add_widget(card_img)

            md_card = PlayingCard(size_hint=(
                1, 1), md_bg_color=(0, 0, 0, 0), card=card)
            md_card.add_widget(md_card_anchorl)

            self.ids.box_layout.add_widget(md_card)

            width = width + md_card.width

        self.ids.box_layout.width = width


class PlayerSpot(MDBoxLayout):
    name = StringProperty("Player")
    bet = NumericProperty(0)
    current_score = NumericProperty(0)
    total_score = NumericProperty(0)
    card = StringProperty("images/empty_card.png")

########################################################################
#   GENERAL FUNCTIONS
########################################################################


def check_server_life(screen):
    global server_thread
    global client_thread

    client_thread.join(0.1)

    if not client_thread.is_alive() and screen.manager.current in ['lobby', 'game_play', "betting"]:
        game_client.close_client = True
        client_thread.join()
        screen.manager.current = 'play_menu'


def get_card_img_path(card):
    if card is None:
        return "images/empty_card.png"
    return "images/" + card.name.casefold().replace(" ", "_") + ".png"

########################################################################
#   APP
########################################################################


class UpAndDownApp(MDApp):
    def build(self):
        # Create the screen manager
        sm = MDScreenManager()
        sm.add_widget(PlayMenu(name="play_menu"))
        sm.add_widget(Lobby(name="lobby"))
        sm.add_widget(GamePlay(name="game_play"))
        sm.add_widget(Betting(name="betting"))
        return sm


UpAndDownApp().run()
