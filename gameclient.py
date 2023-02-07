import time
import socket
import selectors
import types
from functools import partial

from network_msg_types import PlayerStatus, GameStatus
from network_msg import Message
from namings import *


class GameClient():
    def __init__(self, ip, port):
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sel = selectors.DefaultSelector()

        self.server_ip = ip
        self.server_port = port
        self.close_client = False
        self.name = ""
        self.player_status = PlayerStatus()
        self.game_status = GameStatus()
        self.type = None
        self.transition_time = time.time()

    def run(self):
        self.player_status.name = self.name
        events = selectors.EVENT_WRITE  # Client always writes first
        connection_error = self.client_sock.connect_ex(
            (self.server_ip, self.server_port))
        if connection_error:
            return
        self.client_sock.setblocking(False)
        message = Message(self.sel, self.client_sock,
                          (self.server_ip, self.server_port))
        message.set_write_msg_payload(self.player_status)
        message.deliver_read_msg_callback = partial(
            self.update_status, message=message)
        self.sel.register(self.client_sock, events, data=message)
        try:
            while not self.close_client:
                events = self.sel.select(timeout=1)
                for key, mask in events:
                    message = key.data
                    message.set_write_msg_payload(self.player_status)
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
                            print("Not possible to enter this room!")
                            break
                        else:
                            if mask == selectors.EVENT_READ:
                                time.sleep(0.2)
                # Check for a socket being monitored to continue.
                if not self.sel.get_map():
                    break
            print("Shutting down Client")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            for sel_key in self.sel.get_map().values():
                sel_key.fileobj.close()
            self.sel.close()

    def set_name(self, name):
        self.name = name

    def update_status(self, message):
        self.game_status = message.read_msg

        if self.game_status.state == LOBBY:
            pass  # TODO evaluate this
        elif self.game_status.state in [PLAYING, BETTING]:
            self.transition_time = time.time()
        elif self.game_status.state == RESET_IN_ROUND:
            if time.time() > self.transition_time + TRANSITION_DELAY:
                self.player_status.reset_in_round_data()
        elif self.game_status.state == RESET_ROUND:
            if time.time() > self.transition_time + TRANSITION_DELAY:
                self.player_status.reset_round_data()
