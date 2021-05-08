import datetime
from hashlib import sha256

MAX_ENTRIES_AMOUNT = 5
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
    def __init__(self):
        self.blocks = []
        self.last_block_hash = 0
        
    def addBlock(self, newBlock):
        if (self.isBlockValid(newBlock)):
            self.blocks.append(newBlock)
            self.last_block_hash = newBlock.hash()
            return True
        return False
    
    def isBlockValid(self, block):
        return block.header['prev_hash'] == self.last_block_hash and isCryptographicPuzzleSolved(block)
    
    def getLastHash(self):
        return self.last_block_hash
    
    def printBlockChain(self):
        for block in self.blocks:
            print ('-----------------------------------------------------------------------------')
            print (block)
            print ('-----------------------------------------------------------------------------')