import socket
import selectors
import types
from functools import partial

from network_msg_types import LobbyStatus, LobbyPlayerStatus
from network_msg import Message

# Games states
LOBBY = 1
GAME = 2


class GameServer():
    def __init__(self, ip, port):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setblocking(False)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sel = selectors.DefaultSelector()
        self.sel.register(self.server_sock, selectors.EVENT_READ, data=None)

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
            message.set_write_msg_payload("Hello from the Server!")
            message.deliver_read_msg_callback = partial(
                update_status, server=self, message=message, game_state=self.game_state)
            # data = types.SimpleNamespace(addr=addr, message=message)
            events = selectors.EVENT_READ   # Server always reads first
            self.sel.register(conn, events, data=message)
            self.clients += 1
        else:
            msg = "Game is already running. It is not possible to join now!"
            print(msg)
            conn.send(msg.encode('utf-8'))
            conn.close()

    # def process_comm(self, key, mask):
    #     sock = key.fileobj
    #     socket_data = key.data
    #     if mask & selectors.EVENT_READ:
    #         if self.game_state == LOBBY:
    #             recv_data = pickle.loads(sock.recv(4096))
    #             if isinstance(recv_data, LobbyPlayerStatus):
    #                 print(f"Recv: {recv_data.name} from {socket_data.addr}")
    #                 if recv_data.name not in self.lobby_status.players_list:
    #                     self.lobby_status.add_player(recv_data.name)
    #             else:
    #                 if socket_data.name in self.lobby_status.players_list:
    #                     self.lobby_status.remove_player(socket_data.name)
    #                 print(
    #                     f"Closing connection to {socket_data.name} in {socket_data.addr}")
    #                 self.sel.unregister(sock)
    #                 sock.close()
    #         else:
    #             print("GAME state read not implemented yet")
    #     if mask & selectors.EVENT_WRITE:
    #         if self.game_state == LOBBY:
    #             sock.send(pickle.dumps(self.lobby_status))
    #         else:
    #             print("GAME state write not implemented yet")

    def run(self):
        self.server_sock.bind((self.server_ip, self.server_port))
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
            print("Shutting down Server")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()

# def test_callback(server, message):
#     print("Server got: " + message.read_msg)

import time
def update_status(server, message, game_state):
    if game_state == LOBBY:
        if message.read_msg.name not in server.lobby_status.players_list:
            server.lobby_status.add_player(message.read_msg.name)
            print(str(time.time()) + " - Server got: " + str(message.read_msg.name))
        elif message.read_msg.name == '':
            pass
    else:
        print("GAME: Server got: " + message.read_msg)
