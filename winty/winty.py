import requests
import yaml
import logging
from logging.handlers import TimedRotatingFileHandler

class Winty(object):
    def __init__(self):
        self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # create a file handler
        handler = TimedRotatingFileHandler('winty_log',  when='midnight')
        handler.setLevel(logging.INFO)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(handler)

        self.logger = logger


    def read_pools_config(self, filepath):
        try:
            stream = open(filepath, "r")
            config = yaml.load(stream)
            return config
        except Exception as e:
            logger.error('Failed to open file', exc_info=True)


    def scrape_wallet_data(self, pool_config, wallet_address):
        wallet = None
        r = requests.get(pool_config['endpoint'].format(walletAddress=wallet_address))
        if r.status_code == 200:
            self.logger.debug("Retrieved wallet for %s", wallet_address)
            wallet = r.json()
        else:
            self.logger.error("Failed to retrieve wallet data from %s for wallet %s", pool_config['name'], wallet_address)

        wallet = {key: value for (key, value) in wallet.items() if key in pool_config['fields']}
        return wallet


if __name__ == '__main__':
    w = Winty()
    
    config = w.read_pools_config('winty/pools.yaml')
    w.scrape_wallet_data(config['ahashpool'], '1AWV5n8oDChuympDM78B57X525SZtgeK1W')