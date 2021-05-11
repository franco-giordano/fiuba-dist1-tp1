from common.server import Server
import threading
import logging

class QueriesAPIServer(Server):
    def __init__(self, port, listen_backlog, blockchain_storage):
        Server.__init__(self, port, listen_backlog)
        self.blockchain_storage = blockchain_storage

    def handle_client_connection(self, client_sock):
        t_id = threading.get_ident()
        try:
            block_hash = int(client_sock.recv(4096).rstrip().decode())
            logging.info(f"QUERIES THREAD {t_id}: Received query. Requesting hash {block_hash}")

            self._handle_hash_query(client_sock, block_hash)
        except OSError:
            logging.info(f"BLOCKS THREAD {t_id}: Error while reading socket {client_sock}")
        finally:
            client_sock.close()

    def _handle_hash_query(self, client_sock, block_hash):
        t_id = threading.get_ident()
        block = self.blockchain_storage.get_by_hash(block_hash)
        if block:
            logging.info(f"BLOCKS THREAD {t_id}: Found requested block {block}")
            client_sock.send(b"BLOCK_HASH_FOUND " + block.serialize())
            logging.info(f"BLOCKS THREAD {t_id}: Responded BLOCK_HASH_FOUND to {client_sock.getpeername()}")
        else:
            logging.info(f"BLOCKS THREAD {t_id}: requested block hash not found ({block_hash})")
            client_sock.send(b"BLOCK_HASH_NOT_FOUND")
            logging.info(f"BLOCKS THREAD {t_id}: Responded BLOCK_HASH_NOT_FOUND to {client_sock.getpeername()}")