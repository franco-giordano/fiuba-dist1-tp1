from common.socket_transceiver import SocketTransceiver
from common.blockchain import Block

class BlocksTransceiver(SocketTransceiver):
    def __init__(self, sock):
        SocketTransceiver.__init__(self, sock)
        self.CLIENT_TYPE_SIZE = 16
        self.MAX_BLOCKS_SIZE = 65536 * 257

    def recv_if_client_is_uploader(self):
        cli_type = self.recv_and_strip(self.CLIENT_TYPE_SIZE).decode()

        return cli_type == 'BLOCK_UPLOADER'

    def recv_block(self):
        msg = self.recv_and_strip(self.MAX_BLOCKS_SIZE)
        return Block.deserialize(msg)

    def send_block_accepted(self):
        self.send_strings('BLOCK_ACCEPTED')

    def send_block_rejected(self):
        self.send_strings('BLOCK_REJECTED')

    def send_new_hash_and_diff(self, last_hash, new_diff):
        self.send_strings(str(last_hash), str(new_diff))