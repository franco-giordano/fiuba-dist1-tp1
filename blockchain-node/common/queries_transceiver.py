from common.socket_transceiver import SocketTransceiver
import datetime
import json

class QueriesTransceiver(SocketTransceiver):
    def __init__(self, sock):
        SocketTransceiver.__init__(self, sock)
        self.MAX_QUERY_SIZE = 4096
    
    def recv(self):
        query_list = self.sock.recv(self.MAX_QUERY_SIZE).rstrip().decode().split(' ')

        command = query_list[0]
        if command == 'QUERY_HASH':
            query_list[1] = int(query_list[1])
        elif command == 'QUERY_MINUTE':
            iso_time = query_list[1]
            query_list[1] = datetime.datetime.fromisoformat(iso_time).isoformat(timespec='minutes')

        return query_list

    def send_hash_found(self, block):
        self.send(b"BLOCK_HASH_FOUND " + block.serialize())
    
    def send_hash_not_found(self):
        self.send(b"BLOCK_HASH_NOT_FOUND")
    
    def send_minute_not_found(self):
        self.send(b"BLOCKS_FOR_MINUTE_NOT_FOUND")

    def send_blocks_found_for_minute(self, blocks):
        blocks_serialized = json.dumps(blocks, cls=BlocksListEncoder)
        self.send(b"BLOCKS_FOR_MINUTE_FOUND " + blocks_serialized.encode())


class BlocksListEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Block):
            return obj.serialize_str()
        return json.JSONEncoder.default(self, obj)