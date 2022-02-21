from ast import Return
from binance.client import Client
from binance import BinanceSocketManager
import matplotlib
import pandas as pd
import sqlalchemy
import mplfinance as mpl
import tkinter

EMA_lenght = 10

def findLowestPrice(amount, data):
    lowest = data.CP[0]
    index = 0
    for i in range (0, amount):
        #print (i, ": ", data.CP[i])
        if data.CP[i] < lowest:
            lowest = data.CP[i]
            index = i
    return index

def findHighestPrice(amount, data):
    highest = data.CP[0]
    index = 0
    for i in range (1, amount - 1):
        if data.CP[i] > highest:
            highest = data.CP[i]
            index = i
    return index

def findLower(index, data):
    lower = data.CP[index]
    newIndex = index
    amount = 10
    if (len(data) - index) < 10:
        amount = len(data) - index
    for i in range (index, index + amount):
        if data.CP[i] < lower:
            lower = data.CP[i]
            newIndex = i
    if newIndex == index:
        return -1
    return newIndex

def findHigher(index, data):
    higher = data.CP[index]
    newIndex = index
    amount = 10
    if (len(data) - index) < 10:
        amount = len(data) - index
    for i in range (index, index + amount):
        if data.CP[i] > higher:
            higher = data.CP[i]
            newIndex = i
    if newIndex == index:
        return -1
    return newIndex

def findEMA(data, EMAs = []):
    multiplier = (2 / (EMA_lenght + 1))
    if (len(EMAs) == len(data)):
        data['EMA'] = EMAs
        return (data)
    if (not EMAs):
        PricesSum = 0
        for i in range (0, EMA_lenght):
            PricesSum += data.CP[i]
            if i < (EMA_lenght - 1):
                EMAs.append(0)
        PricesSum /= EMA_lenght
        EMAs.append(PricesSum)
        return findEMA(data, EMAs)

    else:
        currentPrice = data.CP[len(EMAs)]
        EMA = (currentPrice * multiplier) + (EMAs[len(EMAs) - 1] * (1 - multiplier))
        EMAs.append(EMA)
        return findEMA(data, EMAs)

def findSMA(data, periods, SMAs = []):
    title = "SMA" + str(periods)

    if (len(data) == len(SMAs)):
        data[title] = SMAs
        return (data)

    if len(data) < (periods * 1.5):
        print ("not enough data to analyse!")
        return

    while (len(SMAs) < 100):
        SMAs.append(0)

    PricesSum = 0
    for i in range (len(SMAs) - periods, (len(SMAs))):
        PricesSum += data.CP[i]
    PricesSum /= periods
    SMAs.append (PricesSum)
    return findSMA (data, periods, SMAs)

def findDEMA(data, DEMAs = []):
    pass

def displayCharts(data):
    matplotlib.use('TkAgg')
    newData = data.drop(['CT', 'symbol', 'OT'], axis = 1, inplace = False)
    newData.index = pd.DatetimeIndex(data['OT'])
    newData.rename(columns = {'OP': 'Open', 'H': 'High', 'L': 'Low', 'CP': 'Close'}, inplace = True)
    #EMA = mpl.make_addplot(newData["EMA"].values, panel = 0, color = 'fuchsia')
    #floatEMA = []
    #for i in range (0, len(data) - EMA_lenght):
    #    floatEMA.append(int(data.EMA[i + EMA_lenght]))

    #TODO display the EMA

    mpl.plot(newData, type = 'candle', style = 'charles', title = 'BTC Price', mav = (50, 100))  
    mpl.show()

def findCross(data):
    flag = False
    if data.SMA100[0] > data.SMA50[0]:
        flag = True

    for i in range (1, len(data) - 1):
        #print (i)
        if data.SMA100[i] < data.SMA50[i] and flag == True:
            print ("SMA100 and SMA50 croossed around", data.CT[i])
            flag = False
            #return True
        elif data.SMA100[i] > data.SMA50[i] and flag == False:
            print ("SMA100 and SMA50 croossed around", data.CT[i])
            flag = True
            #return True
    #print ("SMA100 and SMA50 have't crossed for the last", len(data) - 1, "days")
    #return False

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    df = pd.read_sql('BTCUSDT', engine)
    data = df.iloc[:]
    data = findEMA(data, [])
    data = findSMA(data, 100, [])
    data = findSMA(data, 50, [])
    print (data)
    findCross(data)
    displayCharts(data)
    #print(findLower(findLowestPrice(5, data), data))

    #for i in range (0, len(data) - 1):
    #    if data.OP[i] > data.CP[i]:
    #        print (data.symbol[i], " is down ", data.OP[i] - data.CP[i], " in the last minute")
    #    elif data.OP[i] < data.CP[i]:
    #        print (data.symbol[i], " is up ", data.CP[i] - data.OP[i], " in the last minute")
    #    elif data.OP[i] == data.CP[i]:
    #        print (data.symbol[i], "'s price hasn't moved in the last minute")
            
    
    #lowest = data.L[1]
    #highest = data.H[1]
    #lowestClose = data.CP[1]
    #highestClose = data.CP[1]
    #for i in range (2, 5):
    #    if data.L[i] < lowest:
    #        lowest = data.L[i]
    #    if data.H[i] > highest:
    #        highest = data.H[i]
    #   if data.CP[i] < lowestClose:
    #        lowestClose = data.CP[i]
    #    if data.CP[i] > highestClose:
    #        highestClose = data.CP[i]

    #print("lowest: ", lowest)
    #print("highest: ", highest)
    #print("lowestClose: ", lowestClose)
    #print("HighestClose: ", highestClose)
    #print (data)
