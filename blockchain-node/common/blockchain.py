import datetime
from hashlib import sha256
import json
import copy
from common.blockchain_storage import BlockchainStorage
from common.block import Block
import logging

# MAX_ENTRIES_AMOUNT = 256
# MAX_BLOCKS_PER_DIFF_UPDATE = 3
# TARGET_TIME_IN_SECONDS = 12

def isCryptographicPuzzleSolved(aBlock):
    return aBlock.hash() < (2**256) / aBlock.header['difficulty'] - 1

class Blockchain:
    def __init__(self, config_params, locks_dir, locks_dir_lock):
        self.blocks = []
        self.last_block_hash = 0
        self.expected_difficulty = 1
        self.start_time = datetime.datetime.now()
        self.blocks_added_since_last_update = 0
        self.storage = BlockchainStorage(config_params['blockchain_root_dir'], locks_dir, locks_dir_lock, config_params['suffix_len'])
        self.MAX_BLOCKS_PER_DIFF_UPDATE = config_params['max_blocks_per_diff_update']
        self.TARGET_TIME_IN_SECONDS = config_params['target_time_in_seconds']
        Block.MAX_CHUNKS_PER_BLOCK = config_params['max_chunks_per_block']
        
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
        if self.blocks_added_since_last_update >= self.MAX_BLOCKS_PER_DIFF_UPDATE:
            elapsed_time = (datetime.datetime.now() - self.start_time).total_seconds()
            self.expected_difficulty = self.expected_difficulty * (self.blocks_added_since_last_update/elapsed_time) * self.TARGET_TIME_IN_SECONDS
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