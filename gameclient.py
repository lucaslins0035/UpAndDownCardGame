import time
import socket
import selectors
import types
from functools import partial

from network_msg_types import LobbyStatus, LobbyPlayerStatus
from network_msg import Message

# Games states
LOBBY = 1
GAME = 2


class GameClient():
    def __init__(self, ip, port):
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sel = selectors.DefaultSelector()

        self.server_ip = ip
        self.server_port = port
        self.close_client = False
        self.game_state = LOBBY
        self.name = ""
        self.lobby_client_state = LobbyPlayerStatus()
        self.lobby_status = LobbyStatus()


    def run(self):
        self.lobby_client_state.name = self.name
        events = selectors.EVENT_WRITE  # Client always writes first
        connection_error = self.client_sock.connect_ex((self.server_ip, self.server_port))
        if connection_error:
            print("Connection error" + str(connection_error))
            return
        self.client_sock.setblocking(False)
        message = Message(self.sel, self.client_sock,
                          (self.server_ip, self.server_port))
        message.set_write_msg_payload(self.lobby_client_state)
        message.deliver_read_msg_callback = partial(
            update_status, client=self, message=message, game_state=self.game_state)
        self.sel.register(self.client_sock, events, data=message)
        try:
            while not self.close_client:
                events = self.sel.select(timeout=1)
                for key, mask in events:
                    message = key.data
                    if self.game_state == LOBBY:
                        message.set_write_msg_payload(self.lobby_client_state)
                    else:
                        message.set_write_msg_payload(
                            "CLIENT: to game mode")
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
                            break
                        else: 
                            if mask == selectors.EVENT_READ:
                                time.sleep(1)
                # Check for a socket being monitored to continue.
                if not self.sel.get_map():
                    break
            print("Shutting down Client")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            events = self.sel.select(timeout=1)
            for key, mask in events:
                key.data.close()

    def set_name(self, name):
        self.name = name


def update_status(client, message, game_state):
    if game_state == LOBBY:
        client.lobby_status = message.read_msg
        print(str(time.time()) + " - Client got: " +
              str(client.lobby_status.players_list))
    else:
        print("GAME: Client got: " + message.read_msg)
