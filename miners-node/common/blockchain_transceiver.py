from common.socket_transceiver import SocketTransceiver

class BlockchainTransceiver(SocketTransceiver):
    def __init__(self, sock):
        SocketTransceiver.__init__(self, sock)
        self.MAX_UPLOAD_RESPONSE_SIZE = 64
        self.MAX_HASH_AND_DIFF_SIZE = 512

    def register_as_uploader(self):
        self.send_strings('BLOCK_UPLOADER')
    
    def register_as_listener(self):
        self.send_strings('BLOCK_LISTENER')

    def send_block(self, block):
        self.send_strings(block.serialize_str())

    def recv_upload_response(self):
        return self.recv_and_strip(self.MAX_UPLOAD_RESPONSE_SIZE).decode()

    def recv_new_hash_and_diff(self):
        data = self.recv_and_strip(self.MAX_HASH_AND_DIFF_SIZE).decode().split()
        return int(data[0]), float(data[1])
