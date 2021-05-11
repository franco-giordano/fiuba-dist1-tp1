import datetime
from hashlib import sha256
import json
import copy
from common.blockchain_storage import BlockchainStorage
import logging

MAX_ENTRIES_AMOUNT = 256
MAX_BLOCKS_PER_DIFF_UPDATE = 3
TARGET_TIME_IN_SECONDS = 12

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

class Blockchain:
    def __init__(self, root_dir, locks_dir, locks_dir_lock):
        self.blocks = []
        self.last_block_hash = 0
        self.expected_difficulty = 1
        self.start_time = datetime.datetime.now()
        self.blocks_added_since_last_update = 0
        self.storage = BlockchainStorage(root_dir, locks_dir, locks_dir_lock)
        
    def addBlock(self, newBlock):
        if (self.isBlockValid(newBlock)):
            self.blocks.append(newBlock)
            self.last_block_hash = newBlock.hash()
            self.storage.store_block(newBlock)
            self._adjust_difficulty()
            return True, self.expected_difficulty
        return False, self.expected_difficulty
    
    def _adjust_difficulty(self):
        self.blocks_added_since_last_update += 1
        if self.blocks_added_since_last_update >= MAX_BLOCKS_PER_DIFF_UPDATE:
            elapsed_time = (datetime.datetime.now() - self.start_time).total_seconds()
            self.expected_difficulty = self.expected_difficulty * (self.blocks_added_since_last_update/elapsed_time) * TARGET_TIME_IN_SECONDS
            self.blocks_added_since_last_update = 0
            self.start_time = datetime.datetime.now()
            logging.info(f"BLOCKCHAIN: Updated difficulty to {self.expected_difficulty}")

    def isBlockValid(self, block):
        logging.info(f"BLOCKCHAIN: Block has correct difficulty {self.expected_difficulty == block.header['difficulty']}")
        return self.expected_difficulty == block.header['difficulty']\
            and block.header['prev_hash'] == self.last_block_hash\
            and isCryptographicPuzzleSolved(block)
    
    def getLastHash(self):
        return self.last_block_hash

    def __str__(self):
        res = '=============================================================================\n'
        for block in self.blocks:
            res += '--VVVVVVVVVVVVVVVVVVVVVVVV---------------------------------------------------\n'
            res += str(block) + '\n'
        res += '=============================================================================\n'
        return res
    
    def printBlockChain(self):
        print(self)