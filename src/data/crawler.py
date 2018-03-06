
import urllib2
import HTMLParser
import re, os
import urlparse
import pandas as pd
from bs4 import BeautifulSoup

# TODO: Parser should be stateless
class CoinMKTCapHistParser(HTMLParser.HTMLParser):

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.table = []
        self.in_tr = False
        self.in_td = False
        self.in_thead = False

    def handle_starttag(self, tag, attrs):
        if tag == 'thead':
            self.in_thead = True
        if tag == 'tr':
            self.in_tr = True
            self.row = []
        if tag == 'td':
            self.in_td = True

    def handle_data(self, data):
        if self.in_td:
            self.row.append(data.lstrip().rstrip())

    def handle_endtag(self, tag):
        if tag == 'tr':
            if self.in_thead == True:
                return
            self.table.append(self.row)
            self.in_tr = False
        if tag == 'td':
            self.in_td = False
        if tag == 'thead':
            self.in_thead = False

class CoinMkttCapHistCrawler(object):

    HIST_INDEX_PAGE = r'https://coinmarketcap.com/historical/'

    COLS = ['Ticker', 'Name', 'MktCap', 'Spot', 'CSupply',
            'Volume', '1h_Chg', '1d_Chg', '7d_Chg']

    DUMPBASE = r'E:\CryptoAlphaTeam\ETF\CCBETF\Data'

    def __init__(self, dumpbase = None):
        self.dates = []
        self.dumpbase = dumpbase or self.DUMPBASE
        self._getHist()
        self.hist = {}

    def _getHist(self):
        response = urllib2.urlopen(self.HIST_INDEX_PAGE)
        html_string = response.read()
        soup = BeautifulSoup(html_string, 'lxml')  # Parse the HTML as a string
        pat = re.compile("historical\/[0-9]+")
        for link in pat.findall(str(soup)):
            self.dates.append(link.partition('/')[2])

    def _parseRow(self, row):
        def convFloat(num):
            try:
                return float(re.sub('[$,%]', '', num))
            except:
                return float('nan')
        name, ticker, mktcap, spot, supply, vol, chg1h, chg1d, chg7d = row[3], row[5], row[8], row[10], row[13], row[
            16], row[18], row[19], row[20]
        mktcap = convFloat(mktcap)
        spot = convFloat(spot)
        supply = convFloat(supply)
        vol = convFloat(vol)
        chg1h = convFloat(chg1h)
        chg1d = convFloat(chg1d)
        chg7d = convFloat(chg7d)
        return [name, ticker, mktcap, spot, supply, vol, chg1h, chg1d, chg7d]

    def _parse(self, date):
        url = urlparse.urljoin(self.HIST_INDEX_PAGE, date)

        response = urllib2.urlopen(url)
        html_string = response.read()

        soup = BeautifulSoup(html_string, 'lxml')  # Parse the HTML as a string

        table = soup.find_all('table')[0]  # Grab the first table

        parser = CoinMKTCapHistParser()
        parser.feed(str(table))

        content = []
        for t in parser.table:
            content.append(self._parseRow(t))

        data = pd.DataFrame(content)
        data.columns = self.COLS
        data = data.set_index('Ticker')
        return data

    def parse(self):
        for date in self.dates:
            self.hist[date] = self._parse(date)
            print self.hist[date]

    def dump(self):
        for dt, df in self.hist.iteritems():
            year, month= dt[:4], dt[4:6]
            directory = os.path.join(self.dumpbase, year, month)
            if not os.path.exists(directory):
                os.makedirs(directory)
            path = os.path.join(directory, dt)
            df.to_csv(path)

from src.util.timer import Timer
crawler = CoinMkttCapHistCrawler()
with Timer('Load'):
    crawler.parse()

with Timer('Dump'):
    crawler.dump()
