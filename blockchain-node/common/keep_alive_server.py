import socket
import logging
from threading import Thread
from common.socket_transceiver import SocketTransceiver

class KeepAliveServer:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.threads = []

    def run(self):
        """
        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        while True:
            sock_transceiver = self.accept_new_connection()
            thread = Thread(target = self.handle_client_connection, args = (sock_transceiver, ))
            thread.start()
            self.threads.append(thread)
        
        for t in self.threads:
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