import pickle
import os
import logging

class BlockchainStorage:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.SUFFIX_LEN = 64
    
    def store_block(self, block):
        block_hash = block.hash()
        path = self._generate_block_suffix_path(block_hash)
        self._create_file_if_not_present(path)
        with open(path, "rb+") as f:
            blocks = pickle.load(f)
            logging.info(f"BLOCKCHAIN STORAGE: Unpickled @ {path} blocks {blocks}")
            blocks[block_hash] = block
            f.seek(0)
            pickle.dump(blocks, f)

        logging.info(f"BLOCKCHAIN STORAGE: Stored block {block_hash}")


    def get_by_hash(self, block_hash):
        path = self._generate_block_suffix_path(block_hash)
        block = None
        try:
            with open(path, "rb") as f:
                blocks = pickle.load(f)
                logging.info(f"BLOCKCHAIN STORAGE: #### Retrieved all blocks {blocks}")

                block = blocks.get(block_hash)
                logging.info(f"BLOCKCHAIN STORAGE: Retrieved block {block} @ {path}")
        except OSError:
            logging.warning(f"BLOCKCHAIN STORAGE: block hash not found {block_hash}")
        
        return block

        return block

    def _create_file_if_not_present(self, path):
        if not os.path.exists(path):
            logging.info(f"BLOCKCHAIN STORAGE: Creating new suffix file @ {path}")
            with open(path, 'wb') as f:
                blocks = {}
                pickle.dump(blocks, f)

    def _generate_block_suffix_path(self, block_hash):
        suffix = str(block_hash)[-self.SUFFIX_LEN:]
        return f"{self.root_dir}/by-suffix/{suffix}.txt"
        # return f"{self.root_dir}/by-suffix/prueba.txt"