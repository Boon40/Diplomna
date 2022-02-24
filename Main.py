from binance.client import Client
from binance import BinanceSocketManager
import matplotlib
from matplotlib import markers
from matplotlib.pyplot import hlines
import pandas as pd
import sqlalchemy
import mplfinance as mpl

EMA_lenght = 10

def findLowestPrice(amount, data):
    lowest = data.ClosePrice[0]
    index = 0
    for i in range (0, amount):
        #print (i, ": ", data.ClosePrice[i])
        if data.ClosePrice[i] < lowest:
            lowest = data.ClosePrice[i]
            index = i
    return index

def findHighestPrice(amount, data):
    highest = data.ClosePrice[0]
    index = 0
    for i in range (1, amount - 1):
        if data.ClosePrice[i] > highest:
            highest = data.ClosePrice[i]
            index = i
    return index

def findLower(index, data):
    lower = data.ClosePrice[index]
    newIndex = index
    amount = 10
    if (len(data) - index) < 10:
        amount = len(data) - index
    for i in range (index, index + amount):
        if data.ClosePrice[i] < lower:
            lower = data.ClosePrice[i]
            newIndex = i
    if newIndex == index:
        return -1
    return newIndex

def findHigher(index, data):
    higher = data.ClosePrice[index]
    newIndex = index
    amount = 10
    if (len(data) - index) < 10:
        amount = len(data) - index
    for i in range (index, index + amount):
        if data.ClosePrice[i] > higher:
            higher = data.ClosePrice[i]
            newIndex = i
    if newIndex == index:
        return -1
    return newIndex

def findEMA(data, EMAs = []):
    priceSum = 0
    while len(EMAs) < 11:
        EMAs.append(0)
        priceSum += data.ClosePrice[len(EMAs)]

    multiplier = (2 / (EMA_lenght + 1))



    if (len(EMAs) == len(data)):
        data['EMA'] = EMAs
        return (data)
    if (not EMAs):
        PricesSum = 0
        for i in range (0, EMA_lenght):
            PricesSum += data.ClosePrice[i]
            if i < (EMA_lenght - 1):
                EMAs.append(0)
        PricesSum /= EMA_lenght
        EMAs.append(PricesSum)
        return findEMA(data, EMAs)

    else:
        currentPrice = data.ClosePrice[len(EMAs)]
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
        PricesSum += data.ClosePrice[i]
    PricesSum /= periods
    SMAs.append (PricesSum)
    return findSMA (data, periods, SMAs)

def findDEMA(data, DEMAs = []):
    pass
    #TODO

def findCross(data):
    flag = False
    ifCrossed = False
    if data.SMA100[0] > data.SMA50[0]:
        flag = True

    for i in range (1, len(data) - 1):
        #print (i)
        if data.SMA100[i] < data.SMA50[i] and flag == True:
            print ("SMA100 and SMA50 croossed around", data.CloseTime[i])
            flag = False
            ifCrossed = True
            #return True
        elif data.SMA100[i] > data.SMA50[i] and flag == False:
            print ("SMA100 and SMA50 croossed around", data.CloseTime[i])
            flag = True
            ifCrossed = True
            #return True
    
    if ifCrossed:
        return False
    print ("SMA100 and SMA50 have't crossed for the last", len(data) - 1, "days")

def biggestTrendFibonacci(data):
    highest = findHighestPrice(len(data), data)
    lowest = findLowestPrice(len(data), data)

    priceDifferential = data.ClosePrice[highest] - data.ClosePrice[lowest]
    firstLine = data.ClosePrice[highest]
    secondLine = data.ClosePrice[highest] - ((priceDifferential / 100) * 23.6)
    thirdLine = data.ClosePrice[highest] - ((priceDifferential / 100) * 38.2)
    forthLine = data.ClosePrice[highest] - ((priceDifferential / 100) * 61.8)
    fifthLine = data.ClosePrice[highest] - ((priceDifferential / 100) * 78.6)
    sixthLine = data.ClosePrice[lowest]

    return [sixthLine, fifthLine, forthLine, thirdLine, secondLine, firstLine]

def deltaLines(lines = []):
    dLines = []

    for currentInterval in range(1,6):
        upLine = lines[currentInterval]
        downLine = lines[currentInterval - 1]
        delta = (upLine - downLine) * 5 / 100
        dLines.append(upLine - delta)
        dLines.append(downLine + delta)
        #dLines.append(downLine)
    #dLines.append(lines[5])
    return dLines

def isCloseToLines(data):
    lines = biggestTrendFibonacci(data)
    isClose = False
    changedInterval = 0

    price = data.ClosePrice[0]

    currentInterval = 0
    for j in lines:
        if price > j:
            currentInterval += 1


    for i in range (0, (len(data) - 1)):
        upLine = lines[currentInterval]
        downLine = lines[currentInterval - 1]
        delta = (upLine - downLine) * 5 / 100
        price = data.ClosePrice[i]

        if currentInterval < 1 or currentInterval > 5:
            print ("Error")
            return

        if price > (upLine - delta):
            if price < upLine + delta and isClose is False:
                print ("Current price is close to the", upLine, "resistance zone -", i)
                isClose = True
            else:
                isClose = False
                print ("A candle closed above the", upLine, "resistance zone -", i)
                currentInterval += 1
                changedInterval = 1

        if price < (downLine + delta):
            if price > downLine - delta and isClose is False:
                print ("Current price is close to the", downLine, "support zone -", i)
                isClose = True
            else:
                isClose = False
                print ("A candle closed below the", downLine, "support zone -", i)
                currentInterval -= 1
                changedInterval = -1

        else:
            if isClose:
                isClose = False
                print ("current price is not close to either of the lines")
                if changedInterval == 0:
                    print("The line broke")
                elif changedInterval > 0:
                    print("bounce up")
                else:
                    print("bounce down")
                changedInterval = False
        print(data.ClosePrice[i], i)

def displayCharts(data):
    matplotlib.use('TkAgg')
    newData = data.drop(['CloseTime', 'Symbol', 'OpenTime'], axis = 1, inplace = False)
    newData.index = pd.DatetimeIndex(data['OpenTime'])
    newData.rename(columns = {'OpenPrice': 'Open', 'High': 'High', 'Low': 'Low', 'ClosePrice': 'Close'}, inplace = True)
    #EMA = mpl.make_addplot(newData["EMA"].values, panel = 0, color = 'fuchsia')
    #floatEMA = []
    #for i in range (0, len(data) - EMA_lenght):
    #    floatEMA.append(int(data.EMA[i + EMA_lenght]))

    #TODO display the EMA

    lines = biggestTrendFibonacci(data)
    dlines = deltaLines(lines)
    alphaLines = []
    for i in range(0, 6):
        alphaLines.append([(data.OpenTime[0], lines[i]), (data.OpenTime[len(newData) - 1], lines[i])])
    for i in range(0, 10):
        alphaLines.append([(data.OpenTime[0], dlines[i]), (data.OpenTime[len(newData) - 1], dlines[i])])
    alphaLines.sort()

    mpl.plot(newData, type = 'candle', style = 'charles', title = 'BTC Price', mav = (50, 100), alines = dict(alines=alphaLines,
                                                                                                              colors=['blue', 'red', 'red'],
                                                                                                              linewidths = 0.5))
    mpl.show()

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    df = pd.read_sql('BTCUSDT', engine)
    data = df.iloc[:]
    data = findEMA(data, [])
    data = findSMA(data, 100, [])
    data = findSMA(data, 50, [])
    #print (data)
    #findCross(data)
    isCloseToLines(data)
    displayCharts(data)

    #print(findLower(findLowestPrice(5, data), data))

    #for i in range (0, len(data) - 1):
    #    if data.OpenPrice[i] > data.ClosePrice[i]:
    #        print (data.Symbol[i], " is down ", data.OpenPrice[i] - data.ClosePrice[i], " in the last minute")
    #    elif data.OpenPrice[i] < data.ClosePrice[i]:
    #        print (data.Symbol[i], " is up ", data.ClosePrice[i] - data.OpenPrice[i], " in the last minute")
    #    elif data.OpenPrice[i] == data.ClosePrice[i]:
    #        print (data.Symbol[i], "'s price hasn't moved in the last minute")
            
    
    #lowest = data.Low[1]
    #highest = data.High[1]
    #lowestClose = data.ClosePrice[1]
    #highestClose = data.ClosePrice[1]
    #for i in range (2, 5):
    #    if data.Low[i] < lowest:
    #        lowest = data.Low[i]
    #    if data.High[i] > highest:
    #        highest = data.High[i]
    #   if data.ClosePrice[i] < lowestClose:
    #        lowestClose = data.ClosePrice[i]
    #    if data.ClosePrice[i] > highestClose:
    #        highestClose = data.ClosePrice[i]

    #print("lowest: ", lowest)
    #print("highest: ", highest)
    #print("lowestClose: ", lowestClose)
    #print("HighestClose: ", highestClose)
    #print (data)