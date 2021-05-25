import socket
import logging
from threading import Thread
import queue
from common.socket_transceiver import SocketTransceiver

class Server:
    def __init__(self, port, listen_backlog, MAX_PENDING_CONNECTIONS=256, WORKERS_AMOUNT=3):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.MAX_PENDING_CONNECTIONS = MAX_PENDING_CONNECTIONS
        self.WORKERS_AMOUNT = WORKERS_AMOUNT
        self.workers_queue = queue.Queue(self.MAX_PENDING_CONNECTIONS)
        self.workers = [Thread(target = self._worker_loop) for _ in range(self.WORKERS_AMOUNT)]

    def _start_workers(self):
        for w in self.workers:
            w.start()

    def _worker_loop(self):
        while True:
            transciever = self.workers_queue.get()
            logging.info(f"SRV WORKER: Will process connection with {transciever.peer_name()}")
            self.handle_client_connection(transciever)

    def run(self):
        """
        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        self._start_workers()

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        while True:
            sock_transceiver = self.accept_new_connection()
            self.workers_queue.put(sock_transceiver)            

        for t in self.workers:
            t.join()

    def handle_client_connection(self, sock_transceiver):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        logging.info("NOT IMPLEMENTED!")
        sock_transceiver.close()

    def _transceiver_from_sock(self, client_sock):
        return SocketTransceiver(client_sock)

    def accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info("Proceed to accept new connections")
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        s = self._transceiver_from_sock(c)
        return s