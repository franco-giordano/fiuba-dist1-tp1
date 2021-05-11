#!/usr/bin/env python3

import os
import time
import logging
from common.chunk_api_server import ChunkAPIServer
import configparser

import socket
from common.miner import Miner
from multiprocessing import Process, Queue
from threading import Thread, Lock

from common.stats_api_server import StatsAPIServer
from common.stats_storage import StatsStorage

NUMER_OF_MINERS = 5

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
		config_params["port"] = int(get_config_key("SERVER_PORT", ini_config))
		config_params["stats_port"] = int(get_config_key("SERVER_STATS_PORT", ini_config))
		config_params["listen_backlog"] = int(get_config_key("SERVER_LISTEN_BACKLOG", ini_config))
		config_params["blockchain_ip"] = get_config_key("SERVER_BLOCKCHAIN_IP", ini_config)
		config_params["blockchain_port"] = int(get_config_key("SERVER_BLOCKCHAIN_PORT", ini_config))
		config_params["stats_file_path"] = get_config_key("STATS_FILE_PATH", ini_config)
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

	pool_queues = []
	stats_miners_queue = Queue()
	miners_procs = []
	for id in range(NUMER_OF_MINERS):
		q = Queue()
		pool_queues.append(q)
		miners_procs.append(Process(target=miner_init, args=(id, q, config_params, stats_miners_queue)))

	for w in miners_procs:
		w.start()

	stats_proc = Process(target=stats_init, args=(config_params, stats_miners_queue))
	stats_proc.start()

	# Initialize server and start server loop
	chunks_server = ChunkAPIServer(config_params["port"], config_params["listen_backlog"], pool_queues)

	new_blocks_listener = Thread(target = blocks_listener_init, args = (chunks_server, config_params))
	new_blocks_listener.start()
	
	chunks_server.run()


def miner_init(id, blocks_queue, config_params, stats_miners_queue):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('blockchain-node', 20000))
	sock.send('1'.encode()) # tell blockchain im a block uploader
	logging.info(f"MINER {id}: connected to blockchain @ {config_params['blockchain_ip']}:{config_params['blockchain_port']}")
	miner = Miner(id, blocks_queue, stats_miners_queue)
	miner.run(sock)

def blocks_listener_init(chunks_server, config_params):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('blockchain-node', 20000))
	sock.send('0'.encode()) # tell blockchain im a block listener
	logging.info(f"LISTENER: connected to blockchain @ {config_params['blockchain_ip']}:{config_params['blockchain_port']}")
	while True:
		last_hash = sock.recv(256).rstrip().decode()
		logging.info(f"LISTENER: new hash {last_hash}")
		chunks_server.new_last_hash(int(last_hash))

def stats_init(config_params, stats_miners_queue):
	storage_lock = Lock()
	stats_storage = StatsStorage(config_params['stats_file_path'])

	new_stats_listener = Thread(target=stats_listener_init, args=(stats_storage, storage_lock, stats_miners_queue))
	new_stats_listener.start()
	logging.info(f"Initialized miner stats listener")

	stats_api = StatsAPIServer(config_params['stats_port'], config_params['listen_backlog'], stats_storage, storage_lock)
	logging.info(f"Initializing Stats Querying API")
	stats_api.run()

def stats_listener_init(stats_storage, storage_lock, stats_miners_queue):
	while True:
		msg = stats_miners_queue.get()
		with storage_lock as sl:
			stats_storage.record_stat(msg.miner_id, msg.was_succesful_upload)


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
