import socket
import selectors
import types
import sys


class GameServer():
    def __init__(self, ip, port):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setblocking(False)
        self.server_sock.bind((ip, port))

        self.sel = selectors.DefaultSelector()
        self.sel.register(self.server_sock, selectors.EVENT_READ, data=None)

        self.clients = 0
        self.server_ip = ip
        self.server_port = port
        self.close_server = False

    def evaluate_connection(self, sock):
        conn, addr = sock.accept()
        self.clients += 1
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def process_comm(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                print(f"Closing connection to {data.addr}")
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print(f"Echoing {data.outb!r} to {data.addr}")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def run(self):
        self.server_sock.listen()
        print(f"Listening on {(self.server_ip, self.server_port)}")
        try:
            while not self.close_server:
                events = self.sel.select(timeout=0.2)
                for key, mask in events:
                    if key.data is None:
                        self.evaluate_connection(key.fileobj)
                    else:
                        self.process_comm(key, mask)
            print("Closing Server")
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()
