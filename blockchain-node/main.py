#!/usr/bin/env python3

import os
import time
import logging
from common.server import Server
import configparser

from common.blockchain import Blockchain, Block
import socket

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

	blockchain = Blockchain()

	# Initialize server and start server loop
	# server = Server(config_params["port"], config_params["listen_backlog"])
	# server.run(blockchain)

	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind(('', config_params["port"]))
	server_socket.listen(config_params["listen_backlog"])

	while True:
		client_sock = __accept_new_connection(server_socket)
		block_received = __handle_client_connection(client_sock)

		result = blockchain.addBlock(block_received)
		logging.info(f"Block {block_received}. Result: {result}")
		blockchain.printBlockChain()

def __handle_client_connection(client_sock):
	"""
	Read message from a specific client socket and closes the socket

	If a problem arises in the communication with the client, the
	client socket will also be closed
	"""
	try:
		msg = client_sock.recv(1024).rstrip()
		logging.info('Message {}'.format(msg))
		newBlock = Block.deserialize(msg)
		logging.info(
			'Message received {}. Block Info: {}'
				.format(client_sock.getpeername(), newBlock))
		# client_sock.send("Your Message has been received: {}\n".format(msg).encode('utf-8'))
	except OSError:
		logging.info("Error while reading socket {}".format(client_sock))
	finally:
		client_sock.close()
	
	return newBlock


def __accept_new_connection(server_socket):
	# Connection arrived
	logging.info("Proceed to accept new connections")
	c, addr = server_socket.accept()
	logging.info('Got connection from {}'.format(addr))
	return c

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
