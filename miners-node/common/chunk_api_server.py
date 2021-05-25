import logging
from common.block import Block
import queue
import threading
from common.server import Server
import copy
from common.chunk_transceiver import ChunkTransceiver

MAX_CHUNKS_PER_BLOCK = 20
MAX_PENDING_CHUNKS = 1024
DISPATCH_TIMEOUT_SECONDS = 10
MAX_CHUNK_SIZE = 65536

class ChunkAPIServer(Server):
    def __init__(self, port, listen_backlog, pool_queues):
        # Initialize server socket
        Server.__init__(self, port, listen_backlog)
        self.last_hash = 0
        self.pool_queues = pool_queues
        self.pending_chunks_queue = queue.Queue(MAX_PENDING_CHUNKS)
        self.dispatch_timer = None
        self.miners_are_busy = False
        self.failed_to_dispatch_queue = False
        self.block_difficulty = 1
        self.timer_lock = threading.Lock()
        self.diff_hash_lock = threading.Lock()
        self.build_block_lock = threading.Lock()

    def _transceiver_from_sock(self, sock):
        return ChunkTransceiver(sock)

    # In new thread
    def handle_client_connection(self, chunk_transceiver):
        t_id = threading.get_ident()
        try:
            chunk = chunk_transceiver.recv_chunk()

            if len(chunk) > MAX_CHUNK_SIZE:
                chunk_transceiver.send_too_big()
                logging.info(f'THREAD {t_id}: Received and responded CHUNK_TOO_BIG to {chunk_transceiver.peer_name()}. Chunk Length: {len(chunk)}')
                return

            logging.info(f'THREAD {t_id}: Chunk received from connection {chunk_transceiver.peer_name()}. Chunk: {chunk}')
            success = self._add_to_chunk_queue(chunk, t_id)
            if success:
                logging.info(f'THREAD {t_id}: Responded CHUNK_ACCEPTED to {chunk_transceiver.peer_name()}')
                chunk_transceiver.send_chunk_accepted(chunk)
            else:
                logging.info(f'THREAD {t_id}: Responded CHUNK_DISCARDED to {chunk_transceiver.peer_name()}')
                chunk_transceiver.send_chunk_discarded()
        except OSError:
            logging.info(f"Error while reading socket with {chunk_transceiver.peer_name()}")
        finally:
            chunk_transceiver.close()

    def _add_to_chunk_queue(self, chunk, t_id):
        added = False

        with self.build_block_lock as lck:
            try:
                self.pending_chunks_queue.put_nowait(chunk)
                added = True
            except queue.Full:
                added = False

        if added:
            logging.info(f"THREAD {t_id}: Chunk {chunk} succesfully added to queue.")
            self._destroy_dispatch_timer(t_id)
            self._wait_or_force_dispatch(t_id)
        else:
            logging.error(f"THREAD {t_id}: Chunk queue already full! Discarding chunk: {chunk}")

        return added

    def _wait_or_force_dispatch(self, t_id):
        if self.pending_chunks_queue.qsize() >= MAX_CHUNKS_PER_BLOCK:
            logging.info(f"THREAD {t_id}: Reached max chunks per block, forcing dispatch")
            self._build_and_dispatch_block("REACHED_BLOCK_SIZE")
        else:
            with self.timer_lock as lck:
                self.dispatch_timer = threading.Timer(DISPATCH_TIMEOUT_SECONDS, self._build_and_dispatch_block, args=("TIMER_FINISHED",))
                self.dispatch_timer.start()
                logging.info(f"THREAD {t_id}: Set new timer for dispatch, triggering in {DISPATCH_TIMEOUT_SECONDS} seconds")

    def new_last_hash_and_diff(self, last_hash, new_diff):
        if not self.miners_are_busy:
            logging.error(f"!!!!!!!!!!!!!!!!!! This state is invalid! A new block was added and miners werent working!")

        self.miners_are_busy = False

        with self.diff_hash_lock as dhl:
            self.last_hash = last_hash
            self.block_difficulty = new_diff

        # TODO: probar reemplazar failed_to_dispatch_queue por un llamado a _wait_or_force_dispatch
        self._wait_or_force_dispatch(threading.get_ident())

        # if self.failed_to_dispatch_queue:
        #     logging.info(f"Detected previous failed dispatch attempt. Forcing one now...")
        #     self._build_and_dispatch_block("FAILED_PREV_DISPATCH")

    def _build_and_dispatch_block(self, reason=""):
        with self.build_block_lock as lck:
            self._destroy_dispatch_timer()

            logging.info(f"Block building triggered, will process {self.pending_chunks_queue.qsize()} chunks.")

            if self.miners_are_busy: # or self.failed_to_dispatch_queue:
                logging.warning(f"Failed to dispatch: Miners are busy or new block is being added, cant dispatch now. Waiting for newer hash...")
                self.failed_to_dispatch_queue = True
            else:
                new_block = self._enqueue_and_build_block()
                self._dispatch_block(new_block, reason)
                logging.info(f"!!FILTRAME Pend Chunks Queue is now at: {self.pending_chunks_queue.qsize()}/{MAX_CHUNKS_PER_BLOCK}")

    def _enqueue_and_build_block(self):
        entries = []
        amount = 0
        while amount < MAX_CHUNKS_PER_BLOCK and not self.pending_chunks_queue.empty():
            entries.append(self.pending_chunks_queue.get_nowait())
            amount += 1

        new_block = Block(entries)
        return new_block
    
    def _dispatch_block(self, block, reason):
        if self.miners_are_busy:
            logging.warning(f"!!!!!!!!!!!!!!!!!! Trying to dispatch while miners are busy! Something went wrong!")

        if block.header['entries_amount'] == 0:
            logging.error(f"!!!!!!!!!!!!!!!!!! Tried to dispatch an empty block! Skipping dispatch...")
            return

        with self.diff_hash_lock as dhl:
            block.header['difficulty'] = self.block_difficulty
            block.header['prev_hash'] = self.last_hash

        logging.info(f"!!FILTRAME Block built with prev_hash {block.header['prev_hash']} and {block.header['entries_amount']} entries. Reason: {reason} Dispatching...")

        self.failed_to_dispatch_queue = False
        self.miners_are_busy = True
        for p in self.pool_queues:
            p.put(copy.deepcopy(block))

        logging.info(f"Success dispatching block with prev_hash {block.header['prev_hash']}.")
        
        # if block.header['prev_hash'] in self.already_dispatched_prev_hashes:
        #     logging.error(f"!!!!!!!!!!!!!!!!!! !!!!!!!!!!!!!!!!!!! Dispatched an already dispatched prev_hash {block.header['prev_hash']}! It has {block.header['entries_amount']} entries.")
        # self.already_dispatched_prev_hashes.append(block.header['prev_hash'])
    
    def _destroy_dispatch_timer(self, t_id=None):
        with self.timer_lock as lck:
            if self.dispatch_timer:
                self.dispatch_timer.cancel()
                logging.info(f"THREAD {t_id}: Cancelled previous dispatch timer.")

            self.dispatch_timer = None