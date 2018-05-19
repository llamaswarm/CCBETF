# -*- coding: utf-8 -*-
#import pandas as pd
#import numpy as np
from datetime import datetime
from datetime import timedelta
import os
import logging
import sys
#import numpy as np
#import operator

class Backtest_Account:
    def __init__(self, _NetLiq, num = 2):   #num: 多少个产品
        self.cash = _NetLiq
        self.fixed_baseCap = self.cash
        self.productnum = num
        self.hold_Qt = []
        for i in range(self.productnum):
            self.hold_Qt.append(0)
        self.TC = []
        for i in range(self.productnum):
            self.TC.append(0.00045)
        self.record = {'NetLiq':{},'Holding':{}, 'Ratio':{}}
        self.NetLiq = self.cash
        self.cumTC = 0
        self.Use_Capital_Mode = 0  #0: liq, 1: initial cash

        self.PriceHist = []

    def print_param(self):
        result ="Backtest Account Parameters:\nInitial Cash = " + str(self.cash) + "\nTC = " + str(self.TC)
        return result

    def update_Liq(self, cur_T, mktPrices, logger = None):
        self.NetLiq = self.cash
        for i in range(self.productnum):
            self.NetLiq += self.hold_Qt[i] * mktPrices[i]
        #self.NetLiq = self.cash + self.hold_Qt * mktP
        self.record['NetLiq'].update({cur_T:self.NetLiq})
        self.PriceHist.append([cur_T, self.NetLiq])

        # if not(logger is None):
        #    logger.info((str(cur_T) + ": NetLiq = " + str(self.NetLiq) + ", Hold = " + str(self.hold_Qt)) +", price = " + str(mktP) + ", Lev = " + "{0:.2f}".format(self.hold_Qt * #mktP / self.NetLiq) + ", cumTC = " + "{0:.1f}".format(self.cumTC) +", CapitalMode = " + capital_mode)

    def getLiqRecord(self):
        return self.record['NetLiq']
    
    #Qts 数组，每个产品的量
    #LimPrices 价格， 每个产品的价格
    def order_to(self, Qts, LimPrices, T):
        for i in range(len(Qts)):
            # if(Qts[i] == 0):
            #     tmp_tc = abs(LimPrices[i] * self.hold_Qt[i] * self.TC[i])
            #     self.cash = self.cash + LimPrices[i] * self.hold_Qt[i] - tmp_tc
            #     self.cumTC = self.cumTC + tmp_tc
            #     self.hold_Qt[i] = 0
            if(Qts[i] >0):
                #买了新的
                tmp_tc = Qts[i] * LimPrices[i] * self.TC[i]
                self.cumTC = self.cumTC + tmp_tc
                self.cash = self.cash - LimPrices[i] * Qts[i] - tmp_tc
                self.hold_Qt[i] = self.hold_Qt[i] + Qts[i]
            elif(Qts[i] <0):
                tmp_tc = abs(Qts[i] * LimPrices[i] * self.TC[i])
                self.cumTC = self.cumTC + tmp_tc
                self.cash = self.cash - LimPrices[i] * Qts[i] - tmp_tc
                self.hold_Qt[i] = self.hold_Qt[i] + Qts[i]
            print 'Qt', i, 'TC', tmp_tc, 'Cash Change',  - LimPrices[i] * Qts[i] - tmp_tc
                
        #print("%s" % (self.hold_Qt))
        
        self.record['Holding'].update({T:self.hold_Qt})
        return






