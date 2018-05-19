# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
import os
import logging
import sys
import numpy as np
import operator
import json
import sys
from Futtrade_Common import FutTrade
from Futtrade_Account import Backtest_Account
#from mygetdata import Get_Hist_Date
#from help_func import Cal_PnL_Ratio
#from Turtle_Account import Real_Account
import time
import traceback
from time import sleep

G_LAST_PRINT_POSITION_TIME = 0


def deamon():
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)
    # decouple from parent environment
    os.chdir("./")
    os.setsid()
    os.umask(0)
    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print eventual PID before
            print "Daemon PID %d" % pid
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)


def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    
    return logger


ctime = str(datetime.now())
logger = setup_logger('BTC_PnL', "test.log")

def main():
    #plotly.tools.set_credentials_file(username='sunjoke399', api_key='IzsJsbgZOoKFpLcpG1WK')

    ########################
    myAccount = Backtest_Account(_NetLiq=10000)
    # logger = setup_logger()
    
    my_stg = FutTrade(_account = myAccount, leverage=3)
    
    # datefile1 = "mydata_bch_usd_okexfut_thisweek.log"
    # datefile2 = "mydata_bch_usd_okexfut_nextweek.log"

    datefile1 = r"E:\CryptoAlphaTeam\ETF\CCBETF\src\modules\future\crossexp\mydata_bch_usd_okexfut_thisweek.log"
    datefile2 = r"E:\CryptoAlphaTeam\ETF\CCBETF\src\modules\future\crossexp\mydata_bch_usd_okexfut_nextweek.log"

    datefile1 = r"E:\CryptoAlphaTeam\ETF\CCBETF\src\modules\future\crossexp\okexfut_20180518\mydata_etc_usd_okexfut_thisweek.log"
    datefile2 = r"E:\CryptoAlphaTeam\ETF\CCBETF\src\modules\future\crossexp\okexfut_20180518\mydata_etc_usd_okexfut_nextweek.log"

    with open(datefile1) as f1:
        with open(datefile2) as f2:
            datas1 = None
            datas2 = None
            while(True):
                if(datas1 is None):
                    line = f1.readline()
                    if("" == line):
                        break
                    datas1 = line.split(",")
                if(datas2 is None):
                    line = f2.readline()
                    if("" == line):
                        break
                    datas2 = line.split(",")
                    
                datetimestr1 = datas1[0][0:19]
                datetimestr2 = datas2[0][0:19]
               
                #print datetimestr1 
                #print datetimestr2 
                if(datetimestr1 > datetimestr2):
                    datas2 = None
                    continue
                elif(datetimestr1 < datetimestr2):
                    datas1 = None
                    continue
                
                if(datetimestr1 == datetimestr2):
                    try:
                        orderbook1 = [[float(datas1[1]), float(datas1[3]), float(datas1[5]), float(datas1[7]), float(datas1[9])], [float(datas1[2]), float(datas1[4]), float(datas1[6]), float(datas1[8]), float(datas1[10])], [float(datas1[11]), float(datas1[13]), float(datas1[15]), float(datas1[17]), float(datas1[19])], [float(datas1[12]), float(datas1[14]), float(datas1[16]), float(datas1[18]), float(datas1[20])]]
                        orderbook2 = [[float(datas2[1]), float(datas2[3]), float(datas2[5]), float(datas2[7]), float(datas2[9])], [float(datas2[2]), float(datas2[4]), float(datas2[6]), float(datas2[8]), float(datas2[10])], [float(datas2[11]), float(datas2[13]), float(datas2[15]), float(datas2[17]), float(datas2[19])], [float(datas2[12]), float(datas2[14]), float(datas2[16]), float(datas2[18]), float(datas2[20])]]
                    except:
                        print datetimestr1, 'datas1', datas1
                        print datetimestr2, 'datas2', datas2
                    my_stg.handle_data(datetime.strptime(datetimestr1, "%Y-%m-%d %H:%M:%S"), [orderbook1, orderbook2])
                    datas1 = None
                    datas2 = None
                    
    #print myAccount.getLiqRecord()
    #print myAccount.record['Holding']
    print("posi: %s" % myAccount.hold_Qt)
    print("netliq: %s" % myAccount.NetLiq)
    print("CumTC: %s" % myAccount.cumTC)

    import pandas as pds
    tbl = pds.DataFrame(myAccount.PriceHist)
    tbl.columns = ['TStamp','NetLiq']
    tbl = tbl.set_index('TStamp')
    tbl.plot()

if __name__ == "__main__":
    #deamon()
    
    try:
        main()
    except Exception,e:
        print(e)
        logger.info("exception:%s", e)
        logger.error(traceback.format_exc())

