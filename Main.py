from binance.client import Client
from binance import BinanceSocketManager
import matplotlib
from matplotlib import markers
from matplotlib import animation
from matplotlib.pyplot import hlines
import pandas as pd
import sqlalchemy
import mplfinance as mpl
import matplotlib.animation as animation
import asyncio

EMA_lenght = 10
global ifGoldenCross



def findLowestPrice(amount, df):
    lowest = df.ClosePrice[0]
    index = 0
    for i in range (0, amount):
        #print (i, ": ", df.ClosePrice[i])
        if df.ClosePrice[i] < lowest:
            lowest = df.ClosePrice[i]
            index = i
    return index

def findHighestPrice(amount, df):
    highest = df.ClosePrice[0]
    index = 0
    for i in range (1, amount - 1):
        if df.ClosePrice[i] > highest:
            highest = df.ClosePrice[i]
            index = i
    return index

def findEMA(df, EMAs = []):
    priceSum = 0
    while len(EMAs) < 11:
        EMAs.append(0)
        priceSum += df.ClosePrice[len(EMAs)]

    multiplier = (2 / (EMA_lenght + 1))



    if (len(EMAs) == len(df)):
        df['EMA'] = EMAs
        return (df)
    if (not EMAs):
        PricesSum = 0
        for i in range (0, EMA_lenght):
            PricesSum += df.ClosePrice[i]
            if i < (EMA_lenght - 1):
                EMAs.append(0)
        PricesSum /= EMA_lenght
        EMAs.append(PricesSum)
        return findEMA(df, EMAs)

    else:
        currentPrice = df.ClosePrice[len(EMAs)]
        EMA = (currentPrice * multiplier) + (EMAs[len(EMAs) - 1] * (1 - multiplier))
        EMAs.append(EMA)
        return findEMA(df, EMAs)

def findSMA(df, periods, SMAs = []):
    title = "SMA" + str(periods)

    if (len(df) == len(SMAs)):
        df[title] = SMAs
        return (df)

    if len(df) < (periods * 1.5):
        print ("not enough df to analyse!")
        return

    while (len(SMAs) < 100):
        SMAs.append(0)

    PricesSum = 0
    for i in range (len(SMAs) - periods, (len(SMAs))):
        PricesSum += df.ClosePrice[i]
    PricesSum /= periods
    SMAs.append (PricesSum)
    return findSMA (df, periods, SMAs)

def findDEMA(df, DEMAs = []):
    pass
    #TODO

def findCross(df, short = False):
    lineSmall = []
    lineBig = []
    SMASmall = 0
    SMABig = 0
    if short:
        lineSmall = df.SMA5
        lineBig = df.SMA15
        SMASmall = 5
        SMABig = 15
    else:
        lineSmall = df.SMA50
        lineBig = df.SMA100
        SMASmall = 50
        SMABig = 100
    ifGoldenCross = False
    ifCrossed = False
    if lineBig[0] < lineSmall[0]:
        ifGoldenCross = True

    for i in range (1, len(df) - 1):
        if lineBig[i] > lineSmall[i] and ifGoldenCross == True:
            print ("There was a death cross at around ", df.CloseTime[i], "- price should go down soon")
            ifGoldenCross = False
            ifCrossed = True
        elif lineBig[i] < lineSmall[i] and ifGoldenCross == False:
            print ("There was a golden cross at around ", df.CloseTime[i], "- price should go up soon")
            ifGoldenCross = True
            ifCrossed = True
    
    if ifCrossed:
        return False
    print ("SMA100 and SMA50 have't crossed for the last", len(df) - 1, "days")

def biggestTrendFibonacci(df):
    highest = findHighestPrice(len(df), df)
    lowest = findLowestPrice(len(df), df)

    priceDifferential = df.ClosePrice[highest] - df.ClosePrice[lowest]
    firstLine = df.ClosePrice[highest]
    secondLine = df.ClosePrice[highest] - ((priceDifferential / 100) * 23.6)
    thirdLine = df.ClosePrice[highest] - ((priceDifferential / 100) * 38.2)
    forthLine = df.ClosePrice[highest] - ((priceDifferential / 100) * 61.8)
    fifthLine = df.ClosePrice[highest] - ((priceDifferential / 100) * 78.6)
    sixthLine = df.ClosePrice[lowest]

    return [sixthLine, fifthLine, forthLine, thirdLine, secondLine, firstLine]

def deltaLines(lines = []):
    dLines = []

    for currentInterval in range(1,6):
        upLine = lines[currentInterval]
        downLine = lines[currentInterval - 1]
        delta = (upLine - downLine) * 5 / 100
        dLines.append(downLine + delta)
        dLines.append(upLine - delta)
    return dLines

def isCloseToLines(df):
    lines = biggestTrendFibonacci(df)
    isClose = False
    changedInterval = 0

    price = df.ClosePrice[0]

    currentInterval = 0
    for j in lines:
        if price > j:
            currentInterval += 1


    for i in range (0, (len(df) - 1)):
        upLine = lines[currentInterval]
        downLine = lines[currentInterval - 1]
        delta = (upLine - downLine) * 5 / 100
        price = df.ClosePrice[i]

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
                print ("current price is not close to either of the lines", i)
                if changedInterval > 0:
                    print("bounce up")
                else:
                    print("bounce down")
                changedInterval = False
            print("nothing happened", i)


def displayCharts(df):
    #matplotlib.use('TkAgg')
    newDF = df.drop(['CloseTime', 'Symbol', 'OpenTime'], axis = 1, inplace = False)
    newDF.index = pd.DatetimeIndex(df['OpenTime'])
    newDF.rename(columns = {'OpenPrice': 'Open', 'High': 'High', 'Low': 'Low', 'ClosePrice': 'Close'}, inplace = True)
    #EMA = mpl.make_addplot(newDF["EMA"].values, panel = 0, color = 'fuchsia')
    #floatEMA = []
    #for i in range (0, len(df) - EMA_lenght):
    #    floatEMA.append(int(df.EMA[i + EMA_lenght]))

    #TODO display the EMA

    lines = biggestTrendFibonacci(df)
    dlines = deltaLines(lines)
    alphaLines = []
    for i in range(0, 6):
        alphaLines.append([(df.OpenTime[0], lines[i]), (df.OpenTime[len(newDF) - 1], lines[i])])
    for i in range(0, 10):
        alphaLines.append([(df.OpenTime[0], dlines[i]), (df.OpenTime[len(newDF) - 1], dlines[i])])
    alphaLines.sort()

    mpl.plot(newDF, type = 'candle', style = 'charles', title = 'BTC Price', mav = (5, 15), alines = dict(alines=alphaLines,
                                                                                                              colors=['blue', 'red', 'red'],
                                                                                                              linewidths = 0.5))
    mpl.show()

def animate(ival, df):
    mpl.plot(df, type='candle', style = 'charles')

async def main(df):
    while True:
        await asyncio.sleep(60)
        dataSize = len(df)
        SMA5 = 0
        SMA15 = 0
        SMA50 = 0
        SMA100 = 0
        for i in range (dataSize - 1, dataSize - 101):
            if i > dataSize - 6:
                SMA5 += df.ClosePrise[i]
            if i > dataSize - 16:
                    SMA15 += df.ClosePrise[i]
            if i > dataSize - 51:
                SMA50 += df.ClosePrise[i]
            SMA100 += df.ClosePrise[i]
        df.SMA5[dataSize - 1] = SMA5 / 5
        df.SMA15[dataSize - 1] = SMA15 / 15
        df.SMA50[dataSize - 1] = SMA50 / 50
        df.SMA100[dataSize - 1] = SMA100 / 100
        print (df)

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    df = pd.read_sql('BTCUSDT', engine)
    df = df.iloc[:]
    df = findEMA(df, [])
    df = findSMA(df, 100, [])
    df = findSMA(df, 50, [])
    df = findSMA(df, 15, [])
    df = findSMA(df, 5, [])
    print (df)
    findCross(df, False)
    displayCharts(df)
    loop = asyncio.get_event_loop()
    loop.create_task(df = df.iloc[1: , :])
    loop.create_task(main(df))
    loop.run_forever()
    