import socket
import logging
from common.blockchain_transceiver import BlockchainTransceiver

class ListenerClient:
    def __init__(self, blockchain_ip, blockchain_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((blockchain_ip, blockchain_port))
        self.blockchain_transceiver = BlockchainTransceiver(sock)

        self.blockchain_transceiver.register_as_listener() # tell blockchain im a block listener
        logging.info(f"LISTENER: connected to blockchain @ {blockchain_ip}:{blockchain_port}")

    def run(self, chunks_server):
        while True:
            last_hash, new_diff = self.blockchain_transceiver.recv_new_hash_and_diff()
            logging.info(f"LISTENER: new hash {last_hash}, new diff {new_diff}")
            chunks_server.new_last_hash_and_diff(last_hash, new_diff)
