from common.socket_transceiver import SocketTransceiver

class ChunkTransceiver(SocketTransceiver):
    MAX_CHUNK_SIZE = 0

    def __init__(self, sock):
        SocketTransceiver.__init__(self, sock)

    def recv_chunk(self):
        return self.recv_decoded(self.MAX_CHUNK_SIZE + 5)

    def send_too_big(self):
        self.send_strings("CHUNK_TOO_BIG\n")

    def send_chunk_accepted(self, chunk):
        self.send_strings("CHUNK_ACCEPTED", chunk, "\n")

    def send_chunk_discarded(self):
        self.send_strings("CHUNK_DISCARDED\n")