import requests
from pool_scrapers import yiimp_scraper

class MetricsScraper(object):
    def __init__(self, logger):
        self.logger = logger
        
    def scrape_metrics(self, pool_config, wallet_address):
        wallet = None
        wallet_page_url = pool_config['wallet_page'].format(walletAddress=wallet_address)
        r = requests.get(wallet_page_url, timeout=10)
        try:
            pool_name = pool_config['name'].lower()
            if r.status_code == 200:
                self.logger.debug("Retrieved wallet page for %s", wallet_address)
                if pool_config['is_yiimp']:
                    scraper = yiimp_scraper.YiimpScraper(self.logger)
                    wallet = scraper.scrape_wallet_data(r.text, pool_config)
            else:
                self.logger.error("Failed to retrieve wallet page from %s for wallet %s", pool_config['name'], wallet_address)

        except Exception as e:
            # No need to do anything, just let the job run again next time
            pass
        
        return wallet

