class SocketTransceiver:
    def __init__(self, sock):
        self.sock = sock
    
    def recv(self):
        pass

    def send(self, payload):
        self.sock.send(payload)

    def close(self):
        self.sock.close()

    def peer_name(self):
        return self.sock.getpeername()
