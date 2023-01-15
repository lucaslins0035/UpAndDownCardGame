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

        self.client_sock.setblocking(False)

    # def process_comm(self, key, mask):
    #     sock = key.fileobj
    #     data = key.data
    #     if mask & selectors.EVENT_READ:
    #         if self.game_state == LOBBY:
    #             recv_data = pickle.loads(sock.recv(1024))
    #             if isinstance(recv_data, LobbyStatus):
    #                 print(f"Received {recv_data.players_list}")
    #             else:
    #                 print(f"Closing connection")
    #                 self.sel.unregister(sock)
    #                 sock.close()
    #     if mask & selectors.EVENT_WRITE:
    #         if self.game_state == LOBBY:
    #             sock.send(pickle.dumps(data.lobby_state))

    def run(self):
        events = selectors.EVENT_WRITE  # Client always writes first
        self.client_sock.connect_ex((self.server_ip, self.server_port))
        message = Message(self.sel, self.client_sock,
                          (self.server_ip, self.server_port))
        # data = types.SimpleNamespace(message=message)
        message.set_write_msg_payload("Hello from the Client!")
        message.deliver_read_msg_callback = partial(
            test_callback, server=self, message=message)
        self.sel.register(self.client_sock, events, data=message)
        try:
            while not self.close_client:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    message = key.data
                    try:
                        message.process_events(mask)
                    except Exception:
                        print(
                            f"Main: Error: Exception for {message.addr}:\n"
                            f"{traceback.format_exc()}"
                        )
                        message.close()
                # Check for a socket being monitored to continue.
                if not self.sel.get_map():
                    break
            print("Shutting down Client")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()

    def set_name(self, name):
        self.name = name


def test_callback(server, message):
    print("Client got: " + message.read_msg)
