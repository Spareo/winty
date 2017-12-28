import requests
from pool_scrapers import yiimp_scraper

class MetricsScraper(object):
    def __init__(self, logger):
        self.logger = logger
        
    def scrape_metrics(self, pool_name, measurement, wallet_address, is_yiimp):
        wallet = None
        wallet_page_url = measurement['scrape'].format(walletAddress=wallet_address)
        r = requests.get(wallet_page_url, timeout=10)
        try:
            if r.status_code == 200:
                self.logger.debug("Retrieved wallet page for %s", wallet_address)
                if is_yiimp:
                    scraper = yiimp_scraper.YiimpScraper(self.logger)
                    wallet = scraper.scrape_wallet_data(r.text, measurement['regex'])
            else:
                self.logger.error("Failed to retrieve wallet page from %s for wallet %s", pool_name, wallet_address)

        except Exception as e:
            # No need to do anything, just let the job run again next time
            pass
        
        return wallet

