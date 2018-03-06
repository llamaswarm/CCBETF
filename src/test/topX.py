
import os, glob
import pandas as pds
import numpy as np

pat = r'E:\CryptoAlphaTeam\ETF\CCBETF\Data\201[3-9]\*\*'
paths = glob.glob(pat)

TOPX = 100

# Lookback for all name that ever exists in TOPX universe
tickers = set()

dfs = []
for p in paths:
    df = pds.read_csv(p)
    dt = p.rpartition("\\")[2]
    dts = [dt] * df.shape[0]
    df.insert(0, column='Date', value=dts)
    res = df.sort_values(by=['MktCap'], ascending=False)[:TOPX]
    dfs.append(res)
    for t in res.Name:
        tickers.add(t)

dfs = pds.concat(dfs, ignore_index=True)
print dfs

tbl = pds.pivot_table(dfs, values=['MktCap', 'Spot', 'CSupply', 'Volume'], index=['Date', 'Name'])
print tbl

# txt dump
# tbl.to_csv(r'E:\CryptoAlphaTeam\ETF\CCBETF\Data\data.csv')

# numpy dump
tickers = np.array(list(tickers))
dts = set(tbl.reset_index().Date)
dts = np.array(sorted([int(dt) for dt in dts]))

# data stored date x name
mktcap = pds.pivot_table(tbl.MktCap.reset_index(), values='MktCap', columns=['Name'], index=["Date"])
spot = pds.pivot_table(tbl.Spot.reset_index(), values='Spot', columns=['Name'], index=["Date"])
csupply = pds.pivot_table(tbl.CSupply.reset_index(), values='CSupply', columns=['Name'], index=["Date"])
# volume = pds.pivot_table(tbl.Volume.reset_index(), values='Volume', columns=['Name'], index=["Date"])

mktcapArray = []
spotArray = []
csupplyArray = []
# volumeArray = []
for t in tickers:
    mktcapArray.append(mktcap[t])
    spotArray.append(spot[t])
    csupplyArray.append(csupply[t])
    # volumeArray.append(volume[t])

mktcapArray = np.array(mktcapArray)
spotArray = np.array(spotArray)
csupplyArray = np.array(csupplyArray)
# volumeArray = np.array(volumeArray)

base = r'E:\CryptoAlphaTeam\ETF\CCBETF\Data\Cache'
np.save(os.path.join(base, 'mktcap'), mktcapArray)
np.save(os.path.join(base, 'spot'), spotArray)
np.save(os.path.join(base, 'csupply'), csupplyArray)
# np.save(os.path.join(base, 'volume'), volumeArray)

np.save(os.path.join(base, 'tickers'), tickers)
np.save(os.path.join(base, 'dates'), dts)

####################################################
# Get Return
def getSpot(data, ticker, start=None, end=None):
    dtidx = np.where([np.logical_and(dts < end, dts > start)])[1]
    tidx = np.where(tickers == ticker)[0]
    return data[tidx, dtidx]

####################################################
# Hold TOPX Strategy
S = np.nan_to_num(spotArray)
M = np.nan_to_num(mktcapArray)

start = 20180101
end = 20180201
top = 20

idx = np.where([np.logical_and(dts < end, dts > start)])[1]
cash = 1e6
portfolio = np.zeros((S.shape[0], idx.shape[0] + 1)) * 1.0
#
topmktcap = np.argsort(M[:, max(idx[0] - 1, 0)])[::-1]
print 'topmktcap', topmktcap
# only hold topX instruments
# TODO: Be careful about missing MktCap Data
wgt = M[:, max(idx[0] - 1, 0)]
wgt[topmktcap[top:]] = 0
wgt = wgt / np.nansum(wgt)
portfolio[:, 0] = wgt * cash

for s, i in enumerate(idx):
    # calculate Holding PNL
    # TODO: Be careful of missing price
    mask = np.logical_and(S[:, i+1] != 0, S[:, i] != 0)
    rtn = np.zeros(S.shape[0]) * 1.0
    rtn[mask] = S[mask, i+1] / S[mask, i]
    # print rtn
    # Total available cash
    cash = np.nansum(portfolio[:, s] * rtn)
    # only hold topX instruments
    topmktcap = np.argsort(M[:, i])[::-1]
    wgt = M[:, i]
    wgt[topmktcap[top:]] = 0
    wgt = wgt / np.nansum(wgt)
    portfolio[:, s+1] = wgt * cash

pnl = np.nansum(portfolio, axis=0)

#########################################################

btc = getSpot(spotArray, 'Bitcoin', start, end)
eth = getSpot(spotArray, 'Ethereum', start, end)

dates = dts[idx]

pnl = pnl / pnl[0]
pnl = pnl[:-1]
btc = btc / btc[0]
eth = eth / eth[0]

import seaborn as sns
from datetime import datetime
sns.set(color_codes=True)

ppdata = []
for i, d in enumerate(dates):
    dt = datetime.strptime(str(d), '%Y%m%d')
    print dt
    ppdata.append([i, '', 'TOP20',  pnl[i]])
    ppdata.append([i, '', 'BTC', btc[i]])
    ppdata.append([i, '', 'ETH', eth[i]])
ppdata = pds.DataFrame(ppdata)
ppdata.columns = ['Date', 'Dummy', 'Kind', 'Price']
sns.tsplot(ppdata, time='Date', unit='Dummy', condition='Kind', value='Price')

print btc
print eth
print pnl