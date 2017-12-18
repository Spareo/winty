import requests
import yaml
import logging
import os
from metrics_handler import MetricsHandler
from metrics_scraper import MetricsScraper
from logging.handlers import TimedRotatingFileHandler

class Winty(object):
    def __init__(self, name):
        self.setup_logger()
        self.metricsHandler = MetricsHandler(self.logger)
        self.name = name

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # create a file handler
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        handler = TimedRotatingFileHandler(os.path.join(log_dir,'winty.log'),  when='midnight')
        handler.setLevel(logging.INFO)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(handler)

        self.logger = logger


    def run(self):
        self.logger.info("Winty run started...")
        pool_configs = self.read_pools_config(os.path.dirname(os.path.abspath(__file__)) + '/pools.yaml')
        wallets = self.read_wallet_addresses(os.path.dirname(os.path.abspath(__file__)) + '/wallets.yaml')

        for config in pool_configs.values():
            for wallet in wallets:
                
                if config['datasource'] == "rest":
                    data = self.get_wallet_data(config, wallet)
                else:
                    data = self.scrape_wallet_data(config, wallet)

                values_dict = {}
                tags_dict = {}

                # Set the metric name to use the value from the fields dictionary in pools.yaml
                for (metric_name, metric_value) in data.items():
                    if metric_name in config['fields']:
                        values_dict[config['fields'][metric_name]] = metric_value

                tags_dict['format'] = config['format']
                tags_dict['pool'] = config['name']

                self.logger.info("Pushing metrics for {}".format(config['name']))
                self.metricsHandler.write_metric(self.name, values_dict, tags_dict)
        self.logger.info("Winty finished.")

    def read_pools_config(self, filepath):
        try:
            stream = open(filepath, "r")
            config = yaml.load(stream)
            return config
        except Exception as e:
            self.logger.error('Failed to open file', exc_info=True)


    def read_wallet_addresses(self, filepath):
        try:
            stream = open(filepath, "r")
            wallets = yaml.load(stream)
            return wallets['addresses']
        except Exception as e:
            self.logger.error('Failed to open file', exc_info=True)


    def get_wallet_data(self, pool_config, wallet_address):
        wallet = None
        r = requests.get(pool_config['endpoint'].format(walletAddress=wallet_address))
        try:
            if r.status_code == 200:
                self.logger.debug("Retrieved wallet for %s", wallet_address)
                wallet = r.json()
            else:
                self.logger.error("Failed to retrieve wallet data from %s for wallet %s", pool_config['name'], wallet_address)

            wallet = {key: value for (key, value) in wallet.items() if key in pool_config['fields'].keys()}
        except Exception as e:
            # No need to do anything, just let the job run again next time
            pass

        return wallet


    def scrape_wallet_data(self, pool_config, wallet_address):
        scraper = MetricsScraper(self.logger)
        wallet_data = scraper.scrape_metrics(pool_config, wallet_address)

        return wallet_data

if __name__ == '__main__':
    w = Winty("Winty")
    w.run()
