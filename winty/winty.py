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
                tags_dict = {}
                tags_dict['format'] = config['format']
                tags_dict['pool'] = config['name']
                tags_dict['wallet'] = wallet
                for measurement in config['measurements']:  
                    if measurement['datasource'] == "rest":
                        data = self.get_data_through_rest(measurement, measurement['fields'], config['name'], wallet)
                    else:
                        data = self.get_data_through_scraping(config, measurement, wallet)

                    # Set the metric name to use the value from the fields dictionary in pools.yaml
                    if data is not None:
                        if measurement['name'] == "wallet":
                            self.create_values_and_push(config['name'], measurement, tags_dict, data)
                        elif measurement['name'] == "miners":
                            for miner in data[0]['miners']:
                                tags_dict['algo_tag'] = miner['algo']
                                tags_dict['miner_program'] = miner.pop('version')
                                miner['accepted'] = float(miner['accepted'])
                                miner['rejected'] = float(miner['rejected'])
                                miner['difficulty'] = float(miner['difficulty'])
                                if "," in miner['password']:
                                    split_password = miner['password'].split(",")
                                    miner.pop('password')
                                    miner['currency'] = split_password[0].lstrip("c=")
                                    tags_dict['mined_currency'] = miner.pop('currency')
                                    miner['password'] = split_password[1]
                                    tags_dict['rig'] = miner.pop('password')
                                self.create_values_and_push(config['name'], measurement, tags_dict, miner)
                    else:
                        self.logger.info("Wallet " + wallet + " has no data for " + config['name'] + ".")
                
                    
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


    def get_data_through_rest(self, endpoint_config, fields, pool_name, wallet_address):
        wallet = None
        wallet_data = None

        r = requests.get(endpoint_config['rest'].format(walletAddress=wallet_address), timeout=10)
        try:
            if r.status_code == 200:
                self.logger.debug("Retrieved wallet for %s", wallet_address)
                wallet = r.json()
            else:
                self.logger.error("Failed to retrieve wallet data from %s for wallet %s", pool_name, wallet_address)

            if endpoint_config['name'] == 'miners':
                wallet_data = []
                wallet_data.append({
                    'miners': [
                        {
                            key: value for (key, value) in miners.items() if key in fields.keys()
                        }
                        for miners in wallet['miners']
                    ]
                })
            else:
                wallet_data = {key: value for (key, value) in wallet.items() if key in fields.keys()}
        except Exception as e:
            # No need to do anything, just let the job run again next time
            self.logger.error(e)
            pass

        return wallet_data


    def get_data_through_scraping(self, pool_config, measurement, wallet_address):
        scraper = MetricsScraper(self.logger)
        wallet_data = scraper.scrape_metrics(pool_config['name'], measurement, wallet_address, pool_config['is_yiimp'])

        return wallet_data


    def create_values_and_push(self, pool_name, measurement, tags_dict, data):
        values_dict = {}
        for (metric_name, metric_value) in data.items():
            if metric_name in measurement['fields'] and measurement['fields'][metric_name]:
                values_dict[measurement['fields'][metric_name]] = metric_value

        self.logger.info("Pushing metrics for {}".format(pool_name))
        if measurement['name'] == 'wallet':
            self.metricsHandler.write_metric(self.name, values_dict, tags_dict)
        else:
            self.metricsHandler.write_metric(measurement['name'], values_dict, tags_dict)


if __name__ == '__main__':
    w = Winty("Winty")
    w.run()
