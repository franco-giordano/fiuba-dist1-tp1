import pickle
import os
import logging
import threading
import datetime

class BlockchainStorage:
    def __init__(self, root_dir, locks_dir, locks_dir_lock):
        self.root_dir = root_dir
        self.SUFFIX_LEN = 64
        self.locks_dir = locks_dir
        self.locks_dir_lock = locks_dir_lock
    
    def store_block(self, block):
        self._store_by_suffix(block)
        self._store_by_hour(block)
        
    def _store_by_suffix(self, block):
        block_hash = block.hash()
        sfx_path = self._generate_block_suffix_path(block_hash)

        self._create_sfx_file_if_not_present(sfx_path, block_hash)
        file_lock = self._get_suffix_lock(block_hash)
        with file_lock as lck, open(sfx_path, "rb+") as f:
            blocks = pickle.load(f)
            logging.info(f"BLOCKCHAIN STORAGE: Unpickled @ {sfx_path} blocks {blocks}")
            blocks[block_hash] = block
            f.seek(0)
            pickle.dump(blocks, f)

        logging.info(f"BLOCKCHAIN STORAGE: Stored suffixed block {block_hash} @ {sfx_path}")

    def _store_by_hour(self, block):
        minute = self._generate_minutes_only(block)
        hr_path = self._generate_block_hourly_path(block)
        self._create_hrly_file_if_not_present(hr_path, block)
        
        file_lock = self._get_hourly_lock(block)
        with file_lock as lck, open(hr_path, "rb+") as f:
            by_minute = pickle.load(f)
            logging.info(f"BLOCKCHAIN STORAGE: Unpickled @ {hr_path} blocks by minute {by_minute}")

            if minute not in by_minute:
                by_minute[minute] = []

            by_minute[minute].append(block)
            f.seek(0)
            pickle.dump(by_minute, f)

        logging.info(f"BLOCKCHAIN STORAGE: Stored hourly block for minute {minute} @ {hr_path}")


    def get_by_hash(self, block_hash):
        path = self._generate_block_suffix_path(block_hash)
        block = None
        try:
            file_lock = self._get_suffix_lock(block_hash)
            with file_lock as lck, open(path, "rb") as f:
                blocks = pickle.load(f)
                logging.info(f"BLOCKCHAIN STORAGE: #### Retrieved all blocks {blocks}")

                block = blocks.get(block_hash)
                logging.info(f"BLOCKCHAIN STORAGE: Retrieved block {block} @ {path}")
        except (OSError, KeyError) as e:
            logging.warning(f"BLOCKCHAIN STORAGE: block hash not found {block_hash}. Error {e}")
        
        return block

    def get_by_minute(self, iso_minutes):
        iso_hour = datetime.datetime.fromisoformat(iso_minutes).isoformat(timespec='hours')
        path = self._generate_hourly_path_from_iso(iso_hour)
        blocks = []
        try:
            file_lock = self._get_hourly_lock_from_iso(iso_hour)
            with file_lock as lck, open(path, "rb") as f:
                by_minute = pickle.load(f)
                logging.info(f"BLOCKCHAIN STORAGE: #### Retrieved all blocks {by_minute}")

                blocks = by_minute.get(iso_minutes, [])
                logging.info(f"BLOCKCHAIN STORAGE: Retrieved blocks {blocks} for minute {iso_minutes} @ {path}")
        except (OSError, KeyError) as e:
            logging.warning(f"BLOCKCHAIN STORAGE: no blocks found for time query {iso_minutes}. Error {e}")
        
        return blocks

    def _get_suffix_lock(self, block_hash):
        suffix = self._generate_suffix_only(block_hash)
        lock = None
        
        with self.locks_dir_lock:
            lock = self.locks_dir['by-suffix'][suffix]

        return lock

    def _get_hourly_lock(self, block):
        hour = self._generate_hourly_only(block)
        return self._get_hourly_lock_from_iso(hour)

    def _get_hourly_lock_from_iso(self, iso_hour):
        lock = None
        
        with self.locks_dir_lock:
            lock = self.locks_dir['by-hour'][iso_hour]

        return lock

    def _create_sfx_file_if_not_present(self, path, block_hash):
        if not os.path.exists(path):
            logging.info(f"BLOCKCHAIN STORAGE: Creating new suffix file @ {path}")

            with open(path, 'wb') as f:
                blocks = {}
                pickle.dump(blocks, f)

            with self.locks_dir_lock as lck:
                sfx = self._generate_suffix_only(block_hash)
                self.locks_dir['by-suffix'][sfx] = threading.Lock()


    def _create_hrly_file_if_not_present(self, path, block):
        if not os.path.exists(path):
            logging.info(f"BLOCKCHAIN STORAGE: Creating new hourly file @ {path}")

            with open(path, 'wb') as f:
                by_minute = {}
                pickle.dump(by_minute, f)

            with self.locks_dir_lock as lck:
                hrly = self._generate_hourly_only(block)
                self.locks_dir['by-hour'][hrly] = threading.Lock()

    def _generate_block_suffix_path(self, block_hash):
        suffix = self._generate_suffix_only(block_hash)
        return f"{self.root_dir}/by-suffix/{suffix}"

    def _generate_block_hourly_path(self, block):
        hour = self._generate_hourly_only(block)
        return f"{self.root_dir}/by-hour/{hour}"

    def _generate_hourly_path_from_iso(self, iso_hour):
        return f"{self.root_dir}/by-hour/{iso_hour}"
    
    def _generate_suffix_only(self, block_hash):
        return str(block_hash)[-self.SUFFIX_LEN:]

    def _generate_hourly_only(self, block):
        return block.get_datetime().isoformat(timespec='hours')

    def _generate_minutes_only(self, block):
        return block.get_datetime().isoformat(timespec='minutes')