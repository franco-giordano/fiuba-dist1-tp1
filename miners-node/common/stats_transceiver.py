from common.socket_transceiver import SocketTransceiver

class StatsTransceiver(SocketTransceiver):
    def __init__(self, sock):
        SocketTransceiver.__init__(self, sock)
        self.MAX_QUERY_SIZE = 4096

    def recv_and_parse(self):
        query_list = self.recv_decoded(self.MAX_QUERY_SIZE).split(' ')
        query_list[1] = int(query_list[1])

        return query_list

    def send_no_stats(self):
        self.send_strings("NO_STATS_FOUND")

    def send_stats(self, miner_id, stats):
        self.send_strings("STATS_MINERID_TOTAL_SUCCESS", str(miner_id), str(stats[0]), str(stats[1]))
