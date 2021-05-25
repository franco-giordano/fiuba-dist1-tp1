import logging
from threading import get_ident
from common.server import Server
from common.chunk_transceiver import ChunkTransceiver
from common.chunk_manager import ChunkManager
from common.block_dispatcher import BlockDispatcher

class ChunkAPIServer(Server):
    def __init__(self, config_params, pool_queues):
        Server.__init__(self, config_params["port"], config_params["listen_backlog"])
        block_dispatcher = BlockDispatcher(pool_queues, config_params['max_chunks_per_block'])
        self.MAX_CHUNK_SIZE = config_params["max_chunk_size"]
        self.chunk_manager = ChunkManager(block_dispatcher, config_params)
        ChunkTransceiver.MAX_CHUNK_SIZE = self.MAX_CHUNK_SIZE

    def _transceiver_from_sock(self, sock):
        return ChunkTransceiver(sock)

    # In new thread
    def handle_client_connection(self, chunk_transceiver):
        t_id = get_ident()
        try:
            chunk = chunk_transceiver.recv_chunk()

            if len(chunk) > self.MAX_CHUNK_SIZE:
                chunk_transceiver.send_too_big()
                logging.info(f'THREAD {t_id}: Received and responded CHUNK_TOO_BIG to {chunk_transceiver.peer_name()}. Chunk Length: {len(chunk)}')
                return

            logging.info(f'THREAD {t_id}: Chunk received from connection {chunk_transceiver.peer_name()}. Chunk: {chunk}')
            success = self.chunk_manager.add_to_chunk_queue(chunk)
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

    def new_last_hash_and_diff(self, last_hash, new_diff):
        self.chunk_manager.new_last_hash_and_diff(last_hash, new_diff)
