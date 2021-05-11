import logging
from common.block import Block
import queue
import threading
from common.server import Server
import copy

MAX_PENDING_CHUNKS = 256
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

    # In new thread
    def handle_client_connection(self, client_sock):
        t_id = threading.get_ident()
        try:
            chunk_b = client_sock.recv(MAX_CHUNK_SIZE + 5).rstrip()

            if len(chunk_b) > MAX_CHUNK_SIZE:
                client_sock.send(f"CHUNK_TOO_BIG\n".encode())
                logging.info(f'THREAD {t_id}: Received and responded CHUNK_TOO_BIG to {client_sock.getpeername()}. Chunk Length: {len(chunk_b)}')
                return

            chunk = chunk_b.decode()
            logging.info(f'THREAD {t_id}: Chunk received from connection {client_sock.getpeername()}. Chunk: {chunk}')
            success = self._add_to_chunk_queue(chunk, t_id)
            if success:
                client_sock.send(f"CHUNK_ACCEPTED {chunk}\n".encode())
                logging.info(f'THREAD {t_id}: Responded CHUNK_ACCEPTED to {client_sock.getpeername()}')
            else:
                client_sock.send("CHUNK_DISCARDED\n".encode())
                logging.info(f'THREAD {t_id}: Responded CHUNK_DISCARDED to {client_sock.getpeername()}')
        except OSError:
            logging.info("Error while reading socket {}".format(client_sock))
        finally:
            client_sock.close()

    def _add_to_chunk_queue(self, chunk, t_id):
        added = False

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
        if self.pending_chunks_queue.full():
            logging.info(f"THREAD {t_id}: Queue is now full, forcing dispatch")
            self._build_and_dispatch_block()
        else:
            with self.timer_lock as lck:
                self.dispatch_timer = threading.Timer(DISPATCH_TIMEOUT_SECONDS, self._build_and_dispatch_block)
                self.dispatch_timer.start()
                logging.info(f"THREAD {t_id}: Set new timer for dispatch, triggering in {DISPATCH_TIMEOUT_SECONDS} seconds")

    def new_last_hash_and_diff(self, last_hash, new_diff):
        if not self.miners_are_busy:
            logging.warning(f"!!!!!!!!!!!!!!!!!!!!!!! WHAT?")
        
        self.miners_are_busy = False

        with self.diff_hash_lock as dhl:
            self.last_hash = last_hash
            self.block_difficulty = new_diff

        if self.failed_to_dispatch_queue:
            logging.info(f"Detected previous failed dispatch attempt. Forcing one now...")
            self.failed_to_dispatch_queue = False
            self._build_and_dispatch_block()

    def _build_and_dispatch_block(self):
        self._destroy_dispatch_timer()

        logging.info(f"Block building triggered, will process {self.pending_chunks_queue.qsize()} chunks.")

        if self.miners_are_busy or self.failed_to_dispatch_queue:
            logging.warning(f"Failed to dispatch: Miners are busy or new block is being added, cant dispatch now. Waiting for newer hash...")
            self.failed_to_dispatch_queue = True
        else:
            new_block = self._enqueue_and_build_block()
            self._dispatch_block(new_block)

    def _enqueue_and_build_block(self):
        entries = []
        while not self.pending_chunks_queue.empty():
            entries.append(self.pending_chunks_queue.get_nowait())

        new_block = Block(entries)
        return new_block
    
    def _dispatch_block(self, block):
        if self.miners_are_busy:
            logging.warning(f"!!!!!!!!!!!!!!!!!! Trying to dispatch while miners are busy! Something went wrong!")

        with self.diff_hash_lock as dhl:
            block.header['difficulty'] = self.block_difficulty
            block.header['prev_hash'] = self.last_hash

        logging.info(f"Block built with prev_hash {block.header['prev_hash']}. Dispatching...")

        self.miners_are_busy = True
        for p in self.pool_queues:
            p.put(copy.deepcopy(block))

        logging.info(f"Success dispatching block with prev_hash {block.header['prev_hash']}.")
    
    def _destroy_dispatch_timer(self, t_id=None):
        with self.timer_lock as lck:
            if self.dispatch_timer:
                self.dispatch_timer.cancel()
                logging.info(f"THREAD {t_id}: Cancelled previous dispatch timer.")

            self.dispatch_timer = None