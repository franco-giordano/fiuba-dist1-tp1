#!/usr/bin/env python3

import os
import time
import logging
from common.server import Server
import configparser

from common.blockchain import Blockchain
from common.new_blocks_server import NewBlocksServer
from common.blockchain_storage import BlockchainStorage
from common.queries_api_server import QueriesAPIServer

import threading

def parse_config_params():
	""" Parse env variables to find program config params

	Function that search and parse program configuration parameters in the
	program environment variables. If at least one of the config parameters
	is not found a KeyError exception is thrown. If a parameter could not
	be parsed, a ValueError is thrown. If parsing succeeded, the function
	returns a map with the env variables
	"""

	config = configparser.ConfigParser()		
	config.read("srv-config.ini")
	ini_config = config['DEV']

	config_params = {}
	try:
		config_params["blocks_port"] = int(get_config_key("BLOCKS_SERVER_PORT", ini_config))
		config_params["queries_port"] = int(get_config_key("QUERIES_SERVER_PORT", ini_config))
		config_params["listen_backlog"] = int(get_config_key("SERVERS_LISTEN_BACKLOG", ini_config))
		config_params['blockchain_root_dir'] = get_config_key("BLOCKCHAIN_ROOT_DIR", ini_config)
		config_params["max_chunks_per_block"] = int(get_config_key("MAX_CHUNKS_PER_BLOCK", ini_config))
		config_params["max_chunk_size"] = int(get_config_key("MAX_CHUNK_SIZE", ini_config))
		config_params["max_blocks_per_diff_update"] = int(get_config_key("MAX_BLOCKS_PER_DIFF_UPDATE", ini_config))
		config_params["target_time_in_seconds"] = int(get_config_key("TARGET_TIME_IN_SECONDS", ini_config))
		config_params["suffix_len"] = int(get_config_key("SUFFIX_LEN", ini_config))
		config_params["pending_conn"] = int(get_config_key("MAX_PENDING_CONNECTIONS", ini_config))
		config_params["workers_amount"] = int(get_config_key("SERVER_WORKERS_AMOUNT", ini_config))
	except ValueError as e:
		raise ValueError("Key could not be parsed. Error: {}. Aborting server".format(e))

	return config_params

def get_config_key(name, config_fallback):
	value = os.getenv(name)

	if not value:
		try:
			value = config_fallback[name]
		except KeyError as e:
			raise KeyError("Key was not found. Error: {} .Aborting server".format(e))
	
	return value

def main():
	initialize_log()
	config_params = parse_config_params()

	suffix_files = os.listdir(f"{config_params['blockchain_root_dir']}/by-suffix")
	by_minute_files = os.listdir(f"{config_params['blockchain_root_dir']}/by-minute")

	locks_dir = create_file_locks(suffix_files, by_minute_files)
	locks_dir_lock = threading.Lock()

	query_api_thread = threading.Thread(target = query_api_init, args = (config_params, locks_dir, locks_dir_lock))
	query_api_thread.start()

	blockchain = Blockchain(config_params, locks_dir, locks_dir_lock)
	new_blocks_server = NewBlocksServer(config_params, blockchain)
	new_blocks_server.run()

	query_api_thread.join()

def create_file_locks(suffix_files, by_minute_files):
	locks = {'by-suffix': {}, 'by-minute': {}}

	for s in suffix_files:
		locks['by-suffix'][s] = threading.Lock()

	for m in by_minute_files:
		locks['by-minute'][m] = threading.Lock()

	logging.info(f'Created file locks for {len(suffix_files) + len(by_minute_files)} files')
	
	return locks

# In new thread
def query_api_init(config_params, locks_dir, locks_dir_lock):
	blockchain_storage = BlockchainStorage(config_params['blockchain_root_dir'], locks_dir, locks_dir_lock, config_params['suffix_len'])
	query_api = QueriesAPIServer(config_params, blockchain_storage)
	query_api.run()

def initialize_log():
	"""
	Python custom logging initialization

	Current timestamp is added to be able to identify in docker
	compose logs the date when the log has arrived
	"""
	logging.basicConfig(
		format='%(asctime)s %(levelname)-8s %(message)s',
		level=logging.INFO,
		datefmt='%Y-%m-%d %H:%M:%S',
	)


if __name__== "__main__":
	main()
