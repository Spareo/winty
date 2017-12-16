import re

class YiimpScraper(object):
    def __init__(self, logger):
        self.logger = logger

    def scrape_wallet_data(self, page_text, pool_config):
        # iterate over the texts and scrape out the data we need
        wallet = {}

        regex = re.compile(pool_config['regex'])
        m = regex.search(page_text)

        for key in tuple( m.groupdict().keys() ):
            wallet[key] = float(m.group(key))

        return wallet
