import queue
from threading import Lock, get_ident
import logging
from common.locked_timer import LockedTimer

MAX_CHUNKS_PER_BLOCK = 20
MAX_PENDING_CHUNKS = 1024
DISPATCH_TIMEOUT_SECONDS = 10

class ChunkManager:
    def __init__(self, block_dispatcher):
        self.block_dispatcher = block_dispatcher
        self.pending_chunks_queue = queue.Queue(MAX_PENDING_CHUNKS)
        self.build_block_lock = Lock()
        self.locked_timer = LockedTimer(DISPATCH_TIMEOUT_SECONDS, self._timer_func)

    def add_to_chunk_queue(self, chunk):
        added = False

        with self.build_block_lock as lck:
            try:
                self.pending_chunks_queue.put_nowait(chunk)
                added = True
            except queue.Full:
                added = False

        t_id = get_ident()

        if added:
            logging.info(f"THREAD {t_id} @ CHUNK MGR: Chunk {chunk} succesfully added to queue.")
            self._wait_or_force_dispatch()
        else:
            logging.error(f"THREAD {t_id} @ CHUNK MGR: Chunk queue already full! Discarding chunk: {chunk}")

        return added

    def _wait_or_force_dispatch(self):
        if self.pending_chunks_queue.qsize() >= MAX_CHUNKS_PER_BLOCK:
            logging.info(f"THREAD {t_id} @ CHUNK MGR: Reached max chunks per block, forcing dispatch")

            self.locked_timer.destroy()
            with self.build_block_lock as lck:
                self.block_dispatcher.build_and_dispatch_block(self.pending_chunks_queue)
        else:
            self.locked_timer.restart()
    
    def _timer_func(self):
        with self.build_block_lock as lck:
            self.block_dispatcher.build_and_dispatch_block(self.pending_chunks_queue)

    def new_last_hash_and_diff(self, last_hash, new_diff):
        self.block_dispatcher.new_last_hash_and_diff(last_hash, new_diff)

        if not self.pending_chunks_queue.empty():
            self._wait_or_force_dispatch()
