#!/usr/bin/env python3

import os
import time
import logging
from common.server import Server
import configparser

from common.miner import Miner
from multiprocessing import Process, Queue

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
		config_params["listen_backlog"] = int(get_config_key("SERVER_LISTEN_BACKLOG", ini_config))
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
	miners_procs = []
	for id in range(NUMER_OF_MINERS):
		q = Queue()
		pool_queues.append(q)
		miners_procs.append(Process(target=miner_init, args=(id, q,)))

	for w in miners_procs:
		w.start()

	# Initialize server and start server loop
	server = Server(config_params["port"], config_params["listen_backlog"])
	server.run(pool_queues, miners_procs)


def miner_init(id, blocks_queue):
	miner = Miner(id, blocks_queue)
	miner.run()


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
