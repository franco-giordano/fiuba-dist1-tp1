from common.server import Server
import threading
import logging
from common.blockchain import Block

def locked_apply(lock, func, args=()):
    with lock as l:
        return func(*args)

class NewBlocksServer(Server):
    def __init__(self, port, listen_backlog, blockchain):
        Server.__init__(self, port, listen_backlog)
        self.blockchain = blockchain
        self.blockchain_lock = threading.Lock()
        self.block_listener_socks = []
        self.listeners_lock = threading.Lock()
    
    def handle_client_connection(self, client_sock):
        t_id = threading.get_ident()
        msg = client_sock.recv(4096).rstrip().decode()
        logging.info(f"BLOCKS THREAD {t_id}: Received connection. Type {msg}")

        if msg == '0':
            self._handle_block_listener(client_sock)
        elif msg == '1':
            self._handle_block_uploader(client_sock)

    def _handle_block_uploader(self, client_sock):
        t_id = threading.get_ident()
        logging.info(f"Registered {client_sock.getpeername()} as Uploader. Waiting for blocks...")
        while True:
            try:
                msg = client_sock.recv(4096).rstrip()
                logging.info(f"BLOCKS THREAD {t_id}: Message {msg}")
                new_block = Block.deserialize(msg)
                logging.info(f"BLOCKS THREAD {t_id}: Message received {client_sock.getpeername()}. Block Hash: {new_block.hash()}")
            except OSError:
                logging.info(f"BLOCKS THREAD {t_id}: Error while reading socket {client_sock}")
            # finally:
            #     client_sock.close()
            
            addition_success, new_diff = locked_apply(self.blockchain_lock, self.blockchain.addBlock, (new_block,))
            logging.info(f"BLOCKS THREAD {t_id}: Attempted to add block with hash {new_block.hash()}. Result: {addition_success}")

            if addition_success:
                locked_apply(self.blockchain_lock, self.blockchain.printBlockChain)
                self._announce_new_block(new_diff)
                client_sock.send(b'BLOCK_ACCEPTED')
            else:
                client_sock.send(b'BLOCK_REJECTED')

    def _handle_block_listener(self, client_sock):
        with self.listeners_lock as lck:
            self.block_listener_socks.append(client_sock)
            logging.info(f"Registered {client_sock.getpeername()} as Listener")

    def _announce_new_block(self, new_diff):
        last_hash = locked_apply(self.blockchain_lock, self.blockchain.getLastHash)
        announcement = f"{last_hash} {new_diff}".encode()

        with self.listeners_lock as lck:
            logging.info(f"Starting to announce new block {announcement} to {len(self.block_listener_socks)} listeners")
            for s in self.block_listener_socks:
                logging.info(f"Announcing new block {announcement} to {s.getpeername()}")
                s.send(announcement)
