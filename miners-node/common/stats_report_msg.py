class StatsReportMsg:
    def __init__(self, miner_id, blockchain_response):
        self.miner_id = miner_id
        self.was_succesful_upload = None
        if blockchain_response == 'BLOCK_REJECTED':
            self.was_succesful_upload = False
        elif blockchain_response == 'BLOCK_ACCEPTED':
            self.was_succesful_upload = True