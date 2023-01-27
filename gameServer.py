import time
import socket
import selectors
import types
from functools import partial

from network_msg_types import LobbyStatus, LobbyPlayerStatus
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
        self.game_state = LOBBY
        self.lobby_status = LobbyStatus()

    def evaluate_connection(self, sock):
        conn, addr = sock.accept()
        if self.game_state == LOBBY:  # No more players allowed during the game
            print(f"Accepted connection from {addr}")
            conn.setblocking(False)
            message = Message(self.sel, conn, addr)
            message.set_write_msg_payload(self.lobby_status)
            message.deliver_read_msg_callback = partial(
                update_status, server=self, message=message, game_state=self.game_state)
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
                        if self.game_state == LOBBY:
                            message.set_write_msg_payload(self.lobby_status)
                        else:
                            message.set_write_msg_payload(
                                "SERVER: state at game mode")
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
                                self.remove_player(
                                    str(message.addr))
            print("Shutting down Server")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            for sel_key in self.sel.get_map().values():
                sel_key.fileobj.close()
            self.sel.close()
            
    def add_player(self, player_name, addr):
        self.players_reg.update({addr: player_name})
        self.lobby_status.update_list(self.players_reg)

    def remove_player(self, addr):
        self.players_reg.pop(addr)
        self.lobby_status.update_list(self.players_reg)

# def test_callback(server, message):
#     print("Server got: " + message.read_msg)


def update_status(server, message, game_state):
    if game_state == LOBBY:
        if str(message.addr) not in server.players_reg.keys():
            server.add_player(
                message.read_msg.name, str(message.addr))
            print(str(time.time()) + " - Server got: " +
                  str(message.read_msg.name))
        # elif message.read_msg.name == '':
        #     pass
        if not server.lobby_status.start_game:
            server.lobby_status.start_game = message.read_msg.start_game
            if server.lobby_status.start_game:
                game_state = GAME
    else:
        print("GAME: Server got: " + message.read_msg)
