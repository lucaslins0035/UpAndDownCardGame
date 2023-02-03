import time
import socket
import selectors
import types
from functools import partial

from network_msg_types import GameStatus
from game_manager import GameManager
from network_msg import Message
from namings import *


class GameServer():
    def __init__(self, ip, port):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setblocking(False)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sel = selectors.DefaultSelector()
        self.sel.register(self.server_sock, selectors.EVENT_READ, data=None)

        self.players_reg = {}
        self.clients = 0
        self.server_ip = ip
        self.server_port = port
        self.close_server = False
        self.game_status = GameStatus()

    def evaluate_connection(self, sock):
        conn, addr = sock.accept()
        if self.game_status.state == LOBBY:  # No more players allowed during the game
            print(f"Accepted connection from {addr}")
            conn.setblocking(False)
            message = Message(self.sel, conn, addr)
            message.set_write_msg_payload(self.game_status)
            message.deliver_read_msg_callback = partial(
                self.update_status, message=message)
            events = selectors.EVENT_READ   # Server always reads first
            self.sel.register(conn, events, data=message)
            self.clients += 1
        else:
            msg = "Game is already running. It is not possible to join now!"
            print(msg)
            conn.send(msg.encode('utf-8'))
            conn.close()

    def run(self):
        try:
            self.server_sock.bind((self.server_ip, self.server_port))
        except:
            print("Not able to use this Address")
            return
        self.server_sock.listen()
        print(f"Listening on {(self.server_ip, self.server_port)}")
        try:
            while not self.close_server:
                events = self.sel.select(timeout=1)
                for key, mask in events:
                    if key.data is None:
                        self.evaluate_connection(key.fileobj)
                    else:
                        message = key.data
                        message.set_write_msg_payload(self.game_status)
                        try:
                            message.process_events(mask)
                        except Exception:
                            print(
                                f"Main: Error: Exception for {message.addr}:\n"
                                f"{traceback.format_exc()}"
                            )
                            message.close()
                        else:
                            if message.sock is None:
                                # If the player has been registered
                                if str(message.addr) in self.players_reg.keys():
                                    self.remove_player(str(message.addr))

                                # If a player leaves during the game
                                if self.game_status.state != LOBBY:
                                    self.game_status.valid_game = False
                                    self.close_server = True

            print("Shutting down Server")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            for sel_key in self.sel.get_map().values():
                sel_key.fileobj.close()
            self.sel.close()

    def add_player(self, player_name, addr):
        self.players_reg.update({addr: player_name})
        self.game_status.update_list(self.players_reg)

    def remove_player(self, addr):
        self.players_reg.pop(addr)
        self.game_status.update_list(self.players_reg)

    def update_status(self, message):
        if self.game_status.state == LOBBY:
            if str(message.addr) not in self.players_reg.keys():
                if message.read_msg.name not in self.players_reg.values():
                    self.add_player(
                        message.read_msg.name, str(message.addr))
                else:
                    message.close()

            if not self.game_status.valid_game:
                self.game_status.valid_game = message.read_msg.start_game
                # Check to init game
                if self.game_status.valid_game:
                    self.game_status.init_game_data()
                    self.game_manager = GameManager(
                        self.game_status.players_list)

                    self.game_manager.setup_next_round()
                    self.game_status.current_wild_card = self.game_manager.current_wild_card
                    self.game_status.update_player_data(
                        self.game_manager.current_hands,
                        self.game_manager.current_playing_index,
                        self.game_manager.current_playing_order)

        elif self.game_status.state == BETTING:
            if self.game_status.player_data[message.read_msg.name]["playing"]:
                if message.read_msg.current_bet is not None:
                    self.game_status.player_data[message.read_msg.name]["current_bet"] = message.read_msg.current_bet
                    self.game_manager.pass_turn()
                    if self.game_manager.current_playing_index is None:  # If there is no one left to bet
                        self.game_status.state = PLAYING
                        self.game_status.screen = "game_play"
                    else:
                        self.game_status.update_player_data(
                            self.game_manager.current_hands,
                            self.game_manager.current_playing_index,
                            self.game_manager.current_playing_order)
        else:
            print("not implemented yet")
