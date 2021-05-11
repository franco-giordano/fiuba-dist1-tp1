import pickle
import os
import logging
import threading

class BlockchainStorage:
    def __init__(self, root_dir, locks_dir, locks_dir_lock):
        self.root_dir = root_dir
        self.SUFFIX_LEN = 64
        self.locks_dir = locks_dir
        self.locks_dir_lock = locks_dir_lock
    
    def store_block(self, block):
        block_hash = block.hash()
        path = self._generate_block_suffix_path(block_hash)
        self._create_file_if_not_present(path, block_hash)

        file_lock = self._get_suffix_lock(block_hash)
        with file_lock as lck, open(path, "rb+") as f:
            blocks = pickle.load(f)
            logging.info(f"BLOCKCHAIN STORAGE: Unpickled @ {path} blocks {blocks}")
            blocks[block_hash] = block
            f.seek(0)
            pickle.dump(blocks, f)

        logging.info(f"BLOCKCHAIN STORAGE: Stored block {block_hash}")


    def get_by_hash(self, block_hash):
        path = self._generate_block_suffix_path(block_hash)
        block = None
        file_lock = self._get_suffix_lock(block_hash)
        try:
            with file_lock as lck, open(path, "rb") as f:
                blocks = pickle.load(f)
                logging.info(f"BLOCKCHAIN STORAGE: #### Retrieved all blocks {blocks}")

                block = blocks.get(block_hash)
                logging.info(f"BLOCKCHAIN STORAGE: Retrieved block {block} @ {path}")
        except OSError:
            logging.warning(f"BLOCKCHAIN STORAGE: block hash not found {block_hash}")
        
        return block

    def _get_suffix_lock(self, block_hash):
        suffix = self._generate_suffix_only(block_hash)
        lock = None
        
        with self.locks_dir_lock:
            lock = self.locks_dir['by-suffix'][suffix]

        return lock

    def _create_file_if_not_present(self, path, block_hash):
        if not os.path.exists(path):
            logging.info(f"BLOCKCHAIN STORAGE: Creating new suffix file @ {path}")

            with open(path, 'wb') as f:
                blocks = {}
                pickle.dump(blocks, f)

            with self.locks_dir_lock as lck:
                sfx = self._generate_suffix_only(block_hash)
                self.locks_dir['by-suffix'][sfx] = threading.Lock()

    def _generate_block_suffix_path(self, block_hash):
        suffix = self._generate_suffix_only(block_hash)
        return f"{self.root_dir}/by-suffix/{suffix}"
    
    def _generate_suffix_only(self, block_hash):
        return str(block_hash)[-self.SUFFIX_LEN:]