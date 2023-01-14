import socket
import selectors
import types
import sys

messages = [b"Message 1 from client.", b"Message 2 from client."]


class GameClient():
    def __init__(self, ip, port):
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sel = selectors.DefaultSelector()

        self.server_ip = ip
        self.server_port = port
        self.close_client = False

        self.client_sock.setblocking(False)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            msg_total=sum(len(m) for m in messages),
            recv_total=0,
            messages=messages.copy(),
            outb=b"",
        )
        self.sel.register(self.client_sock, events, data=data)

    def process_comm(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                print(f"Received {recv_data!r}")
                data.recv_total += len(recv_data)
            if not recv_data or data.recv_total == data.msg_total:
                print(f"Closing connection")
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if not data.outb and data.messages:
                data.outb = data.messages.pop(0)
            if data.outb:
                print(f"Sending {data.outb!r} to connection")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def run(self):
        self.client_sock.connect_ex((self.server_ip, self.server_port))
        try:
            while not self.close_client:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    self.process_comm(key, mask)
            print("Closing Client")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()
