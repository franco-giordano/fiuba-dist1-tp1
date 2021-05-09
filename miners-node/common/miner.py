import datetime
import logging
from common.block import Block, isCryptographicPuzzleSolved

class Miner:
    def __init__(self, id, blocks_queue):
        self.id = id
        self.blocks_queue = blocks_queue

    def run(self, blockchain_socket):
        while True:
            data = self.blocks_queue.get()
            logging.info(f"MINER {self.id}: received block with prev_hash {data.header['prev_hash']}")
            self.mine(data, blockchain_socket)
            logging.info(f"MINER {self.id}: mined {data}")


    def mine(self, block, blockchain_socket):
        # block.header['prev_hash'] = prev_hash
        block.header['timestamp'] = datetime.datetime.now()
        while not isCryptographicPuzzleSolved(block):
            block.header['nonce'] += 1
            block.header['timestamp'] = datetime.datetime.now()
        logging.info(f"MINER {self.id}: mined {block}")

        blockchain_socket.send(block.serialize())
        logging.info(f"MINER {self.id}: sent {block.serialize()}")
