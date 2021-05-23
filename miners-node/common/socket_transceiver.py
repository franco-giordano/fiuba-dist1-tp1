class SocketTransceiver:
    def __init__(self, sock):
        self.sock = sock
    
    def recv_and_strip(self, size):
        return self.sock.recv(size).rstrip()

    def recv_decoded(self, size):
        return self.recv_and_strip(size).decode('utf-8')

    def send_strings(self, *strings_tuple):
        msg = " ".join(strings_tuple)
        self.sock.send(msg.encode('utf-8'))

    def close(self):
        self.sock.close()

    def peer_name(self):
        return self.sock.getpeername()
