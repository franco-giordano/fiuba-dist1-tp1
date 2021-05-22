import datetime
from hashlib import sha256
import json
import copy

MAX_ENTRIES_AMOUNT = 256

def isCryptographicPuzzleSolved(aBlock):
    return aBlock.hash() < (2**256) / aBlock.header['difficulty'] - 1
    
class Block: 
    def __init__(self, entries):
        self.header = {
            'prev_hash': 0,
            'nonce': 0,
            'timestamp': None,
            'entries_amount': len(entries),
            'difficulty': 1
        }
        if (len(entries) <= MAX_ENTRIES_AMOUNT):
            self.entries = entries
        else:
            raise 'Exceeding max block size'
            
    def hash(self):
        return int(sha256(repr(self.header).encode('utf-8') + repr(self.entries).encode('utf-8')).hexdigest(), 16)
    
    def get_datetime(self):
        return self.header['timestamp']

    @staticmethod
    def deserialize(bytes_recv):
        parsed = json.loads(bytes_recv.decode('utf-8'))
        block = Block(parsed['entries'])
        block.header['prev_hash'] = parsed['header']['prev_hash']
        block.header['nonce'] = parsed['header']['nonce']
        block.header['timestamp'] = datetime.datetime.fromisoformat(parsed['header']['timestamp'])
        block.header['entries_amount'] = parsed['header']['entries_amount']
        block.header['difficulty'] = parsed['header']['difficulty']
        return block

    def serialize(self):
        return self.serialize_str().encode('utf-8')

    def serialize_str(self):
        dictionary = copy.deepcopy(self.__dict__)
        dictionary['header']['timestamp'] = dictionary['header']['timestamp'].isoformat()
        return json.dumps(dictionary)

    def __str__(self):
        entries = ",".join(self.entries)
        return """
        'block_hash': {0}
        
        'header': {{
            'prev_hash':{1}
            'nonce': {2}
            'timestamp': {3}
            'entries_amount': {4}
            'difficulty': {5}
        }}
        
        'entries': [
            {6}
        ]
        """.format(hex(self.hash()), hex(self.header['prev_hash']), self.header['nonce'], self.header['timestamp'], self.header['entries_amount'], self.header['difficulty'], entries)
