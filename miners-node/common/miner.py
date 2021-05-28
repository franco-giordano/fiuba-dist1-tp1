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

    def mine(self, block, blockchain_transceiver):
        block.header['nonce'] += self.STARTING_NONCE
        block.header['timestamp'] = datetime.datetime.now()

        while self.blocks_queue.empty() and not isCryptographicPuzzleSolved(block):
            block.header['nonce'] += 1
            block.header['timestamp'] = datetime.datetime.now()

        if not self.blocks_queue.empty():
            logging.info(f"MINER {self.id}: new block to mine received! Someone mined before me. Reporting stat...")
            bad_report = StatsReportMsg.build_rejected_report(self.id)
            self.stats_report_queue.put(bad_report)
            return

        logging.info(f"MINER {self.id}: mined with prev_hash {block.header['prev_hash']}")

        blockchain_transceiver.send_block(block)
        logging.info(f"MINER {self.id}: sent {block.serialize_str()}")

        response = blockchain_transceiver.recv_upload_response()
        logging.info(f"MINER {self.id}: last block result was {response}. Reporting to stats process...")
        report = StatsReportMsg(self.id, response)
        self.stats_report_queue.put(report)
