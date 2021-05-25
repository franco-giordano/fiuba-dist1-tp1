from common.server import Server
import threading
import logging
from common.blockchain import Block
from common.queries_transceiver import QueriesTransceiver

class QueriesAPIServer(Server):
    def __init__(self, config_params, blockchain_storage):
        Server.__init__(self, config_params["queries_port"], config_params["listen_backlog"], config_params['pending_conn'], config_params['workers_amount'])
        self.blockchain_storage = blockchain_storage

    def handle_client_connection(self, queries_transceiver):
        t_id = threading.get_ident()
        try:
            query_list = queries_transceiver.recv_and_parse()
            logging.info(f"QUERIES THREAD {t_id}: Received query {query_list}")

            self.dispatch_query(queries_transceiver, query_list)
        except OSError:
            logging.info(f"QUERIES THREAD {t_id}: Error while reading socket with {queries_transceiver.peer_name()}")
        finally:
            queries_transceiver.close()

    def dispatch_query(self, queries_transceiver, query_list):
        command = query_list[0]
        if command == 'QUERY_HASH':
            self._handle_hash_query(queries_transceiver, query_list[1:])
        elif command == 'QUERY_MINUTE':
            self._handle_minute_query(queries_transceiver, query_list[1:])
        elif command == 'PARSING_ERROR':
            self.handle_parse_error(queries_transceiver)

    def _handle_hash_query(self, queries_transceiver, args):
        block_hash = args[0]
        t_id = threading.get_ident()
        block = self.blockchain_storage.get_by_hash(block_hash)
        if block:
            logging.info(f"QUERIES THREAD {t_id}: Found requested block {block}")
            queries_transceiver.send_hash_found(block)
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCK_HASH_FOUND to {queries_transceiver.peer_name()}")
        else:
            logging.info(f"QUERIES THREAD {t_id}: requested block hash not found ({block_hash})")
            queries_transceiver.send_hash_not_found()
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCK_HASH_NOT_FOUND to {queries_transceiver.peer_name()}")

    def _handle_minute_query(self, queries_transceiver, args):
        t_id = threading.get_ident()
        only_minutes = args[0]
        blocks = self.blockchain_storage.get_by_minute(only_minutes)

        if blocks == []:
            logging.info(f"QUERIES THREAD {t_id}: No blocks found for time {only_minutes}")
            queries_transceiver.send_minute_not_found()
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCKS_FOR_MINUTE_NOT_FOUND to {queries_transceiver.peer_name()}")
        else:
            logging.info(f"QUERIES THREAD {t_id}: Found blocks {blocks} for time {only_minutes}")
            queries_transceiver.send_blocks_found_for_minute(blocks)
            logging.info(f"QUERIES THREAD {t_id}: Responded BLOCK_HASH_FOUND to {queries_transceiver.peer_name()}")

    def handle_parse_error(self, queries_transceiver):
        t_id = threading.get_ident()
        logging.info(f"QUERIES THREAD {t_id}: Responded INVALID_ARGUMENT to {queries_transceiver.peer_name()}")
        queries_transceiver.send_invalid_argument()

    def _transceiver_from_sock(self, sock):
        return QueriesTransceiver(sock)
