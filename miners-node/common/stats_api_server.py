from common.server import Server
import logging
import threading
from common.stats_transceiver import StatsTransceiver

class StatsAPIServer(Server):
    def __init__(self, port, listen_backlog, stats_storage, storage_lock):
        Server.__init__(self, port, listen_backlog)
        self.stats_storage = stats_storage
        self.storage_lock = storage_lock

    def _transceiver_from_sock(self, sock):
        return StatsTransceiver(sock)

    def handle_client_connection(self, stats_transceiver):
        t_id = threading.get_ident()
        try:
            query_list = stats_transceiver.recv_and_parse()
            logging.info(f"STATS QUERIES THREAD {t_id}: Received query {query_list}")

            self.dispatch_query(stats_transceiver, query_list)
        except OSError:
            logging.info(f"STATS QUERIES THREAD {t_id}: Error while reading socket with {stats_transceiver.peer_name()}")
        finally:
            stats_transceiver.close()

    def dispatch_query(self, stats_transceiver, query_list):
        command = query_list[0]
        if command == 'QUERY_MINER':
            self._handle_miner_query(stats_transceiver, query_list[1:])

    def _handle_miner_query(self, stats_transceiver, args):
        miner_id = args[0]
        t_id = threading.get_ident()
        stats = []
        with self.storage_lock as sl:
            stats = self.stats_storage.get_miner_stats(miner_id)

        if stats is None:
            logging.info(f"STATS API THREAD {t_id}: No stats found for miner {miner_id}")
            stats_transceiver.send_no_stats()
            logging.info(f"STATS API THREAD {t_id}: Responded NO_STATS_FOUND to {stats_transceiver.peer_name()}")
        else:
            logging.info(f"STATS API THREAD {t_id}: Found miner {miner_id} stats {stats}")
            stats_transceiver.send_stats(miner_id, stats)
            logging.info(f"STATS API THREAD {t_id}: Responded to {stats_transceiver.peer_name()}")
