from common.server import Server
import logging
import threading

class StatsAPIServer(Server):
    def __init__(self, port, listen_backlog, stats_storage, storage_lock):
        Server.__init__(self, port, listen_backlog)
        self.stats_storage = stats_storage
        self.storage_lock = storage_lock

    def handle_client_connection(self, client_sock):
        t_id = threading.get_ident()
        try:
            query_list = client_sock.recv(4096).rstrip().decode().split(' ')
            logging.info(f"STATS QUERIES THREAD {t_id}: Received query {query_list}")

            self.dispatch_query(client_sock, query_list)
        except OSError:
            logging.info(f"STATS QUERIES THREAD {t_id}: Error while reading socket {client_sock}")
        finally:
            client_sock.close()

    def dispatch_query(self, client_sock, query_list):
        command = query_list[0]
        if command == 'QUERY_MINER':
            self._handle_miner_query(client_sock, query_list[1:])

    def _handle_miner_query(self, client_sock, args):
        miner_id = int(args[0])
        t_id = threading.get_ident()
        stats = []
        with self.storage_lock as sl:
            stats = self.stats_storage.get_miner_stats(miner_id)

        if stats is None:
            logging.info(f"STATS API THREAD {t_id}: No stats found for miner {miner_id}")
            client_sock.send(b"NO_STATS_FOUND")
            logging.info(f"STATS API THREAD {t_id}: Responded NO_STATS_FOUND to {client_sock.getpeername()}")
        else:
            logging.info(f"STATS API THREAD {t_id}: Found miner {miner_id} stats {stats}")
            msg = f"STATS_MINERID_TOTAL_SUCCESS {miner_id} {stats[0]} {stats[1]}"
            client_sock.send(msg.encode())
            logging.info(f"STATS API THREAD {t_id}: Responded {msg} to {client_sock.getpeername()}")