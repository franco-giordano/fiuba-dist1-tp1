import pickle
import logging
import os

class StatsStorage:
    def __init__(self, stats_file_path):
        self.stats_file_path = stats_file_path
        self.stats = {}
        self._build_stats()
    
    def _build_stats(self):
        self._create_if_none()
        with open(self.stats_file_path, 'rb') as f:
            self.stats = pickle.load(f)
        logging.info(f"STATS STORAGE: Built this stats: {self.stats}")

    def _create_if_none(self):
        if not os.path.exists(self.stats_file_path):
            logging.info(f"STATS STORAGE: Creating new stats file @ {self.stats_file_path}")
            with open(self.stats_file_path, 'wb') as f:
                stats = {}
                pickle.dump(stats, f)

    
    def record_stat(self, miner_id, was_succesful_upload):
        if miner_id not in self.stats:
            self.stats[miner_id] = [0,0]

        self.stats[miner_id][0] += 1

        if was_succesful_upload:
            self.stats[miner_id][1] += 1

        # persist in file
        with open(self.stats_file_path, 'wb') as f:
            pickle.dump(self.stats, f)

        logging.info(f"STATS STORAGE: Saved and persisted stat {miner_id} - {self.stats[miner_id]}")
    
    def get_miner_stats(self,miner_id):
        stat = self.stats.get(miner_id)
        logging.info(f"STATS STORAGE: Found stat for {miner_id} - {stat}")
        return stat
