import logging
from common.block import Block
import queue
import threading
from common.server import Server

MAX_PENDING_CHUNKS = 5

class ChunkAPIServer(Server):
    def __init__(self, port, listen_backlog, pool_queues):
        # Initialize server socket
        Server.__init__(self, port, listen_backlog)
        self.last_hash = 0
        self.pool_queues = pool_queues
        self.pending_chunks_queue = queue.Queue(MAX_PENDING_CHUNKS)

    def handle_client_connection(self, client_sock):
        id = threading.get_ident()
        # newBlock = Block(["{{'user_id': 'user_{0}', 'user_data': 'data_{0}'}}".format(1)])
        # newBlock.header['difficulty'] = 1
        # newBlock.header['prev_hash'] = self.last_hash
        try:
            chunk = client_sock.recv(1024).rstrip().decode()
            logging.info(f'THREAD {id}: Chunk received from connection {client_sock.getpeername()}. Chunk: {chunk}')
            success = self._add_to_chunk_queue(chunk, id)
            if success:
                client_sock.send(f"CHUNK_ACCEPTED {chunk}".encode())
                logging.info(f'THREAD {id}: Responded CHUNK_ACCEPTED to {client_sock.getpeername()}')
            else:
                client_sock.send("CHUNK_DISCARDED".encode())
                logging.info(f'THREAD {id}: Responded CHUNK_DISCARDED to {client_sock.getpeername()}')
            # for p in pool_queues:
            #     p.put(newBlock)
            # client_sock.send("Your Message has been received: {}\n".format(msg).encode('utf-8'))
        except OSError:
            logging.info("Error while reading socket {}".format(client_sock))
        finally:
            client_sock.close()

    def _add_to_chunk_queue(self, chunk, id):
        try:
            self.pending_chunks_queue.put_nowait(chunk)
            logging.info(f"THREAD {id}: Chunk {chunk} succesfully added to queue.")
            return True
        except queue.Full:
            logging.error(f"THREAD {id}: Chunk queue already full! Discarding chunk: {chunk}")
            return False

