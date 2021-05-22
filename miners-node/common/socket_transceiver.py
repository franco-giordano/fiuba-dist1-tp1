class SocketTransceiver:
    def __init__(self, sock):
        self.sock = sock
    
    def recv_and_strip(self, size):
        return self.sock.recv(size).rstrip()

    def send_strings(self, *strings_tuple):
        msg = " ".join(strings_tuple)
        self.sock.send(msg.encode())

    def close(self):
        self.sock.close()

    def peer_name(self):
        return self.sock.getpeername()
