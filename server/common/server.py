import socket
import logging
from common.blockchain import Block

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def run(self, pool_queues, miners_procs):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock, pool_queues)


    def __handle_client_connection(self, client_sock, pool_queues):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        newBlock = Block(["{{'user_id': 'user_{0}', 'user_data': 'data_{0}'}}".format(1)])
        newBlock.header['difficulty'] = 1
        newBlock.header['prev_hash'] = 13286618
        try:
            msg = client_sock.recv(1024).rstrip()
            logging.info(
                'Message received from connection {}. Msg: {}'
                    .format(client_sock.getpeername(), msg))
            for p in pool_queues:
                p.put(newBlock)
            client_sock.send("Your Message has been received: {}\n".format(msg).encode('utf-8'))
        except OSError:
            logging.info("Error while reading socket {}".format(client_sock))
        finally:
            client_sock.close()


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info("Proceed to accept new connections")
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c