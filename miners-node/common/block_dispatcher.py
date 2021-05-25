from common.block import Block
import threading
import logging
import copy

MAX_CHUNKS_PER_BLOCK = 20

class BlockDispatcher:
    def __init__(self, pool_queues):
        self.miners_are_busy = False
        self.pool_queues = pool_queues

        self.diff_hash_lock = threading.Lock()
        self.last_hash = 0
        self.block_difficulty = 1.0
    
    def build_and_dispatch_block(self, chunks_queue):
        logging.info(f"Block building triggered, will process {chunks_queue.qsize()} chunks.")

        if self.miners_are_busy:
            logging.warning(f"Failed to dispatch: Miners are busy or new block is being added, cant dispatch now.")
            return

        new_block = self._dequeue_and_build_block(chunks_queue)
        self._dispatch_block(new_block)
        logging.info(f"!!FILTRAME Pend Chunks Queue is now at: {chunks_queue.qsize()}/{MAX_CHUNKS_PER_BLOCK}")

    def _dequeue_and_build_block(self, chunks_queue):
        entries = []
        amount = 0
        while amount < MAX_CHUNKS_PER_BLOCK and not chunks_queue.empty():
            entries.append(chunks_queue.get_nowait())
            amount += 1

        new_block = Block(entries)
        return new_block
    
    def _dispatch_block(self, block):
        if self.miners_are_busy:
            logging.warning(f"!!!!!!!!!!!!!!!!!! Trying to dispatch while miners are busy! Something went wrong!")

        if block.header['entries_amount'] == 0:
            logging.error(f"!!!!!!!!!!!!!!!!!! Tried to dispatch an empty block! Skipping dispatch...")
            return

        with self.diff_hash_lock as dhl:
            block.header['difficulty'] = self.block_difficulty
            block.header['prev_hash'] = self.last_hash

        logging.info(f"!!FILTRAME Block built with prev_hash {block.header['prev_hash']} and {block.header['entries_amount']} entries. Reason: UNKNOWN Dispatching...")

        self.miners_are_busy = True
        for p in self.pool_queues:
            p.put(copy.deepcopy(block))

        logging.info(f"Success dispatching block with prev_hash {block.header['prev_hash']}.")

    def new_last_hash_and_diff(self, last_hash, new_diff):
        if not self.miners_are_busy:
            logging.error(f"!!!!!!!!!!!!!!!!!! This state is invalid! A new block was added and miners werent working!")

        self.miners_are_busy = False

        with self.diff_hash_lock as dhl:
            self.last_hash = last_hash
            self.block_difficulty = new_diff
