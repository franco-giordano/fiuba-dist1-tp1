from common.server import Server
import threading
import logging
import datetime
import json
from common.blockchain import Block

class QueriesAPIServer(Server):
    def __init__(self, port, listen_backlog, blockchain_storage):
        Server.__init__(self, port, listen_backlog)
        self.blockchain_storage = blockchain_storage

    def handle_client_connection(self, client_sock):
        t_id = threading.get_ident()
        try:
            query_list = client_sock.recv(4096).rstrip().decode().split(' ')
            logging.info(f"QUERIES THREAD {t_id}: Received query {query_list}")

            self.dispatch_query(client_sock, query_list)
        except OSError:
            logging.info(f"QUERIES THREAD {t_id}: Error while reading socket {client_sock}")
        finally:
            client_sock.close()

    def dispatch_query(self, client_sock, query_list):
        command = query_list[0]
        if command == 'QUERY_HASH':
            self._handle_hash_query(client_sock, query_list[1:])
        elif command == 'QUERY_MINUTE':
            self._handle_minute_query(client_sock, query_list[1:])

    def _handle_hash_query(self, client_sock, args):
        block_hash = int(args[0])
        t_id = threading.get_ident()
        block = self.blockchain_storage.get_by_hash(block_hash)
        if block:
            logging.info(f"QUERIES THREAD {t_id}: Found requested block {block}")
            client_sock.send(b"BLOCK_HASH_FOUND " + block.serialize())
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCK_HASH_FOUND to {client_sock.getpeername()}")
        else:
            logging.info(f"QUERIES THREAD {t_id}: requested block hash not found ({block_hash})")
            client_sock.send(b"BLOCK_HASH_NOT_FOUND")
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCK_HASH_NOT_FOUND to {client_sock.getpeername()}")

    def _handle_minute_query(self, client_sock, args):
        t_id = threading.get_ident()
        iso_time = args[0]
        only_minutes = datetime.datetime.fromisoformat(iso_time).isoformat(timespec='minutes')
        blocks = self.blockchain_storage.get_by_minute(only_minutes)

        if blocks == []:
            logging.info(f"QUERIES THREAD {t_id}: No blocks found for time {only_minutes}")
            client_sock.send(b"BLOCKS_FOR_MINUTE_NOT_FOUND")
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCKS_FOR_MINUTE_NOT_FOUND to {client_sock.getpeername()}")
        else:
            logging.info(f"QUERIES THREAD {t_id}: Found blocks {blocks} for time {only_minutes}")
            blocks_serialized = json.dumps(blocks, cls=BlocksListEncoder)
            client_sock.send(b"BLOCKS_FOR_MINUTE_FOUND " + blocks_serialized.encode())
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCK_HASH_FOUND to {client_sock.getpeername()}")


class BlocksListEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Block):
            return obj.serialize_str()
        return json.JSONEncoder.default(self, obj)