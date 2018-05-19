# -*- coding: utf-8 -*-
#import pandas as pd
#import numpy as np
from datetime import time as dtime
from datetime import datetime
from datetime import timedelta
import os
import logging
import sys
#import numpy as np
#import operator
import time
import json

import numpy as np

class Signal(object):
    ShortSpread = -1
    Uncertain = 0
    LongSpread = 1

class FutTrade:

    WINDOW = 5400

    EXP_START = dtime(15,30)
    EXP_END = dtime(16,30)
    
    def __init__(self, _account, leverage=1):
        self.myAccount = _account
        self.buystd = 3.5
        self.sellstd = 2
        self.leverage = leverage

        self.__initStats()

    def __initStats(self):
        # Initialize the history
        self.spread = np.empty(self.WINDOW)
        self.spread[:] = np.nan
        self.SignalStates = Signal.Uncertain
        print 'Parameters', 'Window', self.WINDOW, 'BuySTD', self.buystd, 'SellSTD', self.sellstd
        self.spreadall = []

        # Initialize Stats

    def _spread(self, bid1, ask1, bid2, ask2):
        return (bid1 + ask1) / 2 - (bid2 + ask2) / 2

    #******************************************    策略主体   ********************************************
    # 每个周期调用一次，传入orderbook
    # cur_T: 当前时间 datetime.now()
    # orderbooks 每个产品的五层bid ask和量 : [[[bidp1, bidp2, bidp3, bidp4, bidp5],[bidq1, bidq2, bidq3, bidq4, bidq5],[askp1, askp2, askp3, askp4, askp5],[askq1, askq2, bidq3, bidq4, bidq5]], [..], ...]
    def handle_data(self, cur_T, orderbooks):                 
       
        bid1 = orderbooks[0][0][0]
        bidq1 = orderbooks[0][1][0]
        ask1 = orderbooks[0][2][0]
        askq1 = orderbooks[0][3][0]
        
        bid2 = orderbooks[1][0][0]
        bidq2 = orderbooks[1][1][0]
        ask2 = orderbooks[1][2][0]
        askq2 = orderbooks[1][3][0]

        self._updateState(bid1, ask1, bid2, ask2)
        mean, upbuybnd, lobuybnd, upsellbnd, losellbnd = self._updateStats(bid1, ask1, bid2, ask2)
        spread = self._spread(bid1, ask1, bid2, ask2)

        orderpair = (0, 0)
        # TODO: Binary Decision now: Take or let go
        # Better to consider the depth of the orderbook to make it have more capacity
        # and help to lower the cost of the entry level point
        if self.SignalStates == Signal.Uncertain:
            if spread > upbuybnd:
                self.SignalStates = Signal.ShortSpread
                orderpair = (-1, 1)
            elif spread < lobuybnd:
                self.SignalStates = Signal.LongSpread
                orderpair = (1, -1)
        else:
            if self.SignalStates == Signal.LongSpread:
                if spread > upsellbnd:
                    self.SignalStates = Signal.Uncertain
                    orderpair = -1 * np.sign(self.myAccount.hold_Qt)
            elif self.SignalStates == Signal.ShortSpread:
                if spread < losellbnd:
                    self.SignalStates = Signal.Uncertain
                    orderpair = -1 * np.sign(self.myAccount.hold_Qt)

        #print("%s %s" % (cur_T, orderbooks))
        
        # TODO: If it is friday afternoon between 15:30 to 16:30. No trading, Liquidate position
        # Better way to handle this?
        if cur_T.weekday() == 4:
            ctime = cur_T.time()
            if ctime >= self.EXP_START and ctime < self.EXP_END:
                if self.myAccount.hold_Qt != [0, 0]:
                    print '############################################################'
                    print '# Contract Expiring, Liquidate Position'
                    print '############################################################'
                    orderpair = -1 * np.sign(self.myAccount.hold_Qt)
                else:
                    self.myAccount.update_Liq(cur_T, [(bid1 + ask1) / 2, (bid2 + ask2) / 2])
                    return

        order1, order2 = orderpair
        if order1 != 0 or order2 != 0:
            # Decide what price to buy or sell
            orderprice1 = ask1 if order1 > 0 else bid1
            orderprice2 = ask2 if order2 > 0 else bid2
            orderLiq1 = askq1 if order1 > 0 else bidq1
            orderLiq2 = askq2 if order2 > 0 else bidq2

            # Decide How Many Shares to buy
            if self.myAccount.hold_Qt == [0, 0]:
                # Take Integer Lot with the leverage. Take minimum between orderbook liquidity and capital constraint
                share = max(np.floor(self.myAccount.cash / (np.abs(orderprice1) + np.abs(orderprice2))), 1) * self.leverage
                share = np.min([share, orderLiq1, orderLiq2])
                share1 = order1 * share
                share2 = order2 * share
                print 'Enter Position',
            else:
                print 'Liquidate Position',
                share1 = -self.myAccount.hold_Qt[0]
                share2 = -self.myAccount.hold_Qt[1]

            print cur_T, 'Before order', 'Liq', self.myAccount.NetLiq, 'cash', self.myAccount.cash
            self.myAccount.order_to([share1, share2], [orderprice1, orderprice2], cur_T)

            print("posi: %s" % self.myAccount.hold_Qt)
            print cur_T, 'price1', orderprice1 * np.sign(share1), 'q1', orderLiq1, 'price2', orderprice2 * np.sign(share2), 'q2', orderLiq2
            print cur_T, 'spread', spread, 'actual spread', orderprice1 - orderprice2, 'Signal', self.SignalStates
            print cur_T, 'order', [share1, share2], 'Liq', self.myAccount.NetLiq, 'cash', self.myAccount.cash
            # print 'price', spread, upbuybnd, lobuybnd, upsellbnd, losellbnd
            print

        self.myAccount.update_Liq(cur_T, [(bid1+ask1)/2, (bid2+ask2)/2])
        
        # print("netliq %s" % (self.myAccount.NetLiq))
        return

    def _updateStats(self, bid1, ask1, bid2, ask2):
        # spread = min(bid1 - ask2, bid2 - ask1)
        mean = np.nanmean(self.spread)
        std = np.nanstd(self.spread)
        upbuybnd = mean + std * self.buystd
        lobuybnd = mean - std * self.buystd
        upsellbnd = mean + std * self.sellstd
        losellbnd = mean - std * self.sellstd
        return mean, upbuybnd, lobuybnd, upsellbnd, losellbnd

    def _updateState(self, bid1, ask1, bid2, ask2):
        # spread = min(bid1 - bid2, ask1 - ask2)
        spread = self._spread(bid1, ask1, bid2, ask2)
        self.spread = np.roll(self.spread, -1)
        self.spread[-1] = spread
        self.spreadall.append(spread)

    def _stopLoss(self):
        pass