import datetime
import logging
from common.blockchain import Block, isCryptographicPuzzleSolved

class Miner:
    def __init__(self, id, blocks_queue):
        self.id = id
        self.blocks_queue = blocks_queue

    def run(self):
        while True:
            data = self.blocks_queue.get()
            logging.info(f"MINER {self.id}: received {data}")
            self.mine(data)
            logging.info(f"MINER {self.id}: mined {data}")


    def mine(self, block):
        # block.header['prev_hash'] = prev_hash
        block.header['timestamp'] = datetime.datetime.now()
        while not isCryptographicPuzzleSolved(block):
            block.header['nonce'] += 1
            block.header['timestamp'] = datetime.datetime.now()