import datetime
import logging
from common.block import Block, isCryptographicPuzzleSolved
from common.stats_report_msg import StatsReportMsg

class Miner:
    def __init__(self, id, blocks_queue, stats_report_queue):
        self.id = id
        self.blocks_queue = blocks_queue
        self.STARTING_NONCE = self.id * 10000000
        self.stats_report_queue = stats_report_queue

    def run(self, blockchain_transceiver):
        while True:
            data = self.blocks_queue.get()
            logging.info(f"MINER {self.id}: received block with prev_hash {data.header['prev_hash']}")
            self.mine(data, blockchain_transceiver)
            logging.info(f"MINER {self.id}: mined {data}")


    def mine(self, block, blockchain_transceiver):
        block.header['nonce'] += self.STARTING_NONCE
        block.header['timestamp'] = datetime.datetime.now()
        while not isCryptographicPuzzleSolved(block):
            block.header['nonce'] += 1
            block.header['timestamp'] = datetime.datetime.now()
        logging.info(f"MINER {self.id}: mined {block}")

        blockchain_transceiver.send_block(block)
        logging.info(f"MINER {self.id}: sent {block.serialize_str()}")

        response = blockchain_transceiver.recv_upload_response()
        logging.info(f"MINER {self.id}: last block result was {response}. Reporting to stats process...")
        report = StatsReportMsg(self.id, response)
        self.stats_report_queue.put(report)
