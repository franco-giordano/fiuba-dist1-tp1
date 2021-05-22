from common.keep_alive_server import KeepAliveServer
import threading
import logging
from common.blocks_transceiver import BlocksTransceiver

def locked_apply(lock, func, args=()):
    with lock as l:
        return func(*args)

class NewBlocksServer(KeepAliveServer):
    def __init__(self, port, listen_backlog, blockchain):
        KeepAliveServer.__init__(self, port, listen_backlog)
        self.blockchain = blockchain
        self.blockchain_lock = threading.Lock()
        self.block_listener_transceivers = []
        self.listeners_lock = threading.Lock()
    
    def handle_client_connection(self, blocks_transceiver):
        t_id = threading.get_ident()
        is_uploader = blocks_transceiver.recv_if_client_is_uploader()
        logging.info(f"BLOCKS THREAD {t_id}: Received connection. Is uploader: {is_uploader}")

        if is_uploader:
            self._handle_block_uploader(blocks_transceiver)
        else:
            self._handle_block_listener(blocks_transceiver)

    def _handle_block_uploader(self, blocks_transceiver):
        t_id = threading.get_ident()
        logging.info(f"Registered {blocks_transceiver.peer_name()} as Uploader. Waiting for blocks...")
        while True:
            try:
                new_block = blocks_transceiver.recv_block()
                logging.info(f"BLOCKS THREAD {t_id}: Message received {blocks_transceiver.peer_name()}. Block Hash: {new_block.hash()}")
            except OSError:
                logging.info(f"BLOCKS THREAD {t_id}: Error while reading socket with {blocks_transceiver.peer_name()}")
            
            addition_success, new_diff = locked_apply(self.blockchain_lock, self.blockchain.addBlock, (new_block,))
            logging.info(f"BLOCKS THREAD {t_id}: Attempted to add block with hash {new_block.hash()}. Result: {addition_success}")

            if addition_success:
                locked_apply(self.blockchain_lock, self.blockchain.printBlockChain)
                self._announce_new_block(new_diff)
                blocks_transceiver.send_block_accepted()
            else:
                blocks_transceiver.send_block_rejected()

    def _handle_block_listener(self, blocks_transceiver):
        with self.listeners_lock as lck:
            self.block_listener_transceivers.append(blocks_transceiver)
            logging.info(f"Registered {blocks_transceiver.peer_name()} as Listener")

    def _announce_new_block(self, new_diff):
        last_hash = locked_apply(self.blockchain_lock, self.blockchain.getLastHash)

        with self.listeners_lock as lck:
            logging.info(f"Starting to announce new block {last_hash},{new_diff} to {len(self.block_listener_transceivers)} listeners")
            for tr in self.block_listener_transceivers:
                logging.info(f"Announcing new block {last_hash},{new_diff} to {tr.peer_name()}")
                tr.send_new_hash_and_diff(last_hash, new_diff)

    def _transceiver_from_sock(self, sock):
        return BlocksTransceiver(sock)