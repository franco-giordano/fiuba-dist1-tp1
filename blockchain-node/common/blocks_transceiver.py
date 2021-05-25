from common.socket_transceiver import SocketTransceiver
from common.blockchain import Block

class BlocksTransceiver(SocketTransceiver):
    MAX_CHUNKS_PER_BLOCK = 0
    MAX_CHUNK_SIZE = 0
    HEADER_BYTES_SIZE = 101

    def __init__(self, sock):
        SocketTransceiver.__init__(self, sock)
        self.CLIENT_TYPE_SIZE = 16
        self.MAX_BLOCKS_SIZE = self.MAX_CHUNKS_PER_BLOCK * self.MAX_CHUNK_SIZE + self.HEADER_BYTES_SIZE

    def recv_if_client_is_uploader(self):
        cli_type = self.recv_decoded(self.CLIENT_TYPE_SIZE)

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