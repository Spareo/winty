import re
from bs4 import BeautifulSoup

class YiimpScraper(object):
    def __init__(self, logger):
        self.logger = logger

    def scrape_wallet_data(self, page_text):
        soup = BeautifulSoup(page_text, 'html.parser')
        rows = soup.find_all('tr')
        row_texts = [r.text.lower() for r in rows]
        
        # iterate over the texts and scrape out the data we need
        wallet = {}
        for text in row_texts:
            data = re.findall('[.0-9]+', text)
            if 'balance' in text:
                wallet['balance'] = float(data[0]) if len(data) == 1 else None
            elif 'unpaid' in text:
                wallet['unpaid'] = float(data[0]) if len(data) == 1 else None
            elif 'paid' in text:
                wallet['paid'] = float(data[0]) if len(data) == 1 else None
            elif 'earned' in text:
                wallet['total'] = float(data[0]) if len(data) == 1 else None
            elif 'total' in text and 'unpaid' not in text and 'paid' not in text \
                                 and 'earned' not in text and 'confirmed' not in text \
                                 and 'pending' not in text:
                wallet['paid24h'] = float(data[0]) if len(data) == 1 else None

        return wallet
