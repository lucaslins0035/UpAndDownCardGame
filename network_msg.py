import selectors
import pickle
import time


class Message:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self.header = None
        self.deliver_read_msg_callback = lambda: True

        self.read_msg = None  # The content of the msg received from the socket
        self.write_msg_payload = None  # The content of the message to send
        self.write_msg_processed = False  # Whether the write_msg was created or not

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {mode!r}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
            #print(f"Read {data} from {self.addr}")
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            #print(f"Sending {self._send_buffer!r} to {self.addr}")
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]

    def set_write_msg_payload(self, payload):
        self.write_msg_payload = payload

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()

        if self.header is None:
            self.process_header()

        if self.header and self.read_msg is None:
            if len(self._recv_buffer) >= self.header:
                self.process_read_msg()
                self.header = None
                self.deliver_read_msg_callback()
                self.read_msg = None
                self._set_selector_events_mask("w")

    def write(self):
        if (self.write_msg_payload is not None and
                not self.write_msg_processed):
            self.process_write_msg()

        self._write()

        if self.write_msg_processed and not self._send_buffer:
            self._set_selector_events_mask("r")  # Disable write events
            self.write_msg_processed = False

    def close(self):
        # TODO should this method be here?
        print(f"Closing connection to {self.addr}")
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"Error: selector.unregister() exception for "
                f"{self.addr}: {e!r}"
            )

        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.addr}: {e!r}")
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def process_header(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self.header = int.from_bytes(self._recv_buffer[:hdrlen], 'big')
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_read_msg(self):
        data = self._recv_buffer[:self.header]
        self._recv_buffer = self._recv_buffer[self.header:]
        self.read_msg = pickle.loads(data)
        # print(
        #     f"Received {self.header} bytes of "
        #     f"read_msg from {self.addr}"
        # )

    def create_header(self, value):
        header = bytearray(1)
        header.append(len(value))
        if len(header) == 2:
            return header
        return header[1:]

    def process_write_msg(self):
        payload = pickle.dumps(self.write_msg_payload)
        message = self.create_header(payload) + payload
        self._send_buffer += message
        self.write_msg_processed = True

    def get_received_data(self):
        tmp = self.read_msg
        self.read_msg = None
        return tmp
