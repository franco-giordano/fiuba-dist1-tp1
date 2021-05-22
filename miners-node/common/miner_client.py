import logging
from common.miner import Miner
from common.blockchain_transceiver import BlockchainTransceiver
import socket

class MinerClient:
    def __init__(self, blockchain_ip, blockchain_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((blockchain_ip, blockchain_port))

        self.blockchain_transceiver = BlockchainTransceiver(sock)

        self.blockchain_transceiver.register_as_uploader() # tell blockchain im a block uploader
        logging.info(f"MINER {id}: connected to blockchain @ {blockchain_ip}:{blockchain_port}")
        
    def run(self, id, blocks_queue, stats_miners_queue):
        self.miner = Miner(id, blocks_queue, stats_miners_queue)
        self.miner.run(self.blockchain_transceiver)
