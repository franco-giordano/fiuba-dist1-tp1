from common.socket_transceiver import SocketTransceiver
from common.blockchain import Block

class BlocksTransceiver(SocketTransceiver):
    def __init__(self, sock):
        SocketTransceiver.__init__(self, sock)
        self.CLIENT_TYPE_SIZE = 16
        self.MAX_BLOCKS_SIZE = 65536 * 257

    def recv_if_client_is_uploader(self):
        cli_type = self.sock.recv(self.CLIENT_TYPE_SIZE).rstrip().decode()

        return cli_type == '1'

    def recv_block(self):
        msg = self.sock.recv(self.MAX_BLOCKS_SIZE).rstrip()
        return Block.deserialize(msg)

    def send_block_accepted(self):
        self.send(b'BLOCK_ACCEPTED')

    def send_block_rejected(self):
        self.send(b'BLOCK_REJECTED')

    def send_new_hash_and_diff(self, last_hash, new_diff):
        announcement = f"{last_hash} {new_diff}".encode()
        self.send(announcement)