from common.server import Server
import threading
import logging
from common.blockchain import Block

class NewBlocksServer(Server):
    def __init__(self, port, listen_backlog, blockchain):
        Server.__init__(self, port, listen_backlog)
        self.blockchain = blockchain
        self.block_listener_socks = []
    
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
                logging.info(f"BLOCKS THREAD {t_id}: Message received {client_sock.getpeername()}. Block Info: {new_block}")
            except OSError:
                logging.info(f"BLOCKS THREAD {t_id}: Error while reading socket {client_sock}")
            # finally:
            #     client_sock.close()
            
            addition_success = self.blockchain.addBlock(new_block)
            logging.info(f"BLOCKS THREAD {t_id}: Attempted to add block with hash {new_block.hash()}. Result: {addition_success}")

            if addition_success:
                self.blockchain.printBlockChain()
                self._announce_new_block()

    def _handle_block_listener(self, client_sock):
        self.block_listener_socks.append(client_sock)
        logging.info(f"Registered {client_sock.getpeername()} as Listener")

    def _announce_new_block(self):
        # id = threading.get_ident()
        # with open(f"/blockchain-files/{id}.txt", "w") as file:
        #     file.write(str(self.blockchain))

        last_hash_b = str(self.blockchain.getLastHash()).encode()
        logging.info(f"Starting to announce new block {last_hash_b} to {len(self.block_listener_socks)} listeners")
        for s in self.block_listener_socks:
            logging.info(f"Announcing new block {last_hash_b} to {s.getpeername()}")
            s.send(last_hash_b)
