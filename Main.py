from audioop import add
from curses import def_shell_mode
from xml.dom import NotFoundErr
from binance.client import Client
from binance import BinanceSocketManager
import matplotlib
from matplotlib import markers
from matplotlib import animation
from matplotlib.pyplot import hlines
import pandas as pd
import sqlalchemy
import mplfinance as mpl
from matplotlib import pyplot as plt
import matplotlib.animation as animation
import asyncio

from Database import init_db, db_session
from Models import Notification, Signal

init_db()

EMA_lenght = 10
ifGoldenCross = False
isClose = False
lowVol = False
notificationCount = 0


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

def findDEMA(df, DEMAs = []):
    pass
    #TODO

def findCross(df, start, short = False):
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
    global ifGoldenCross
    if lineBig[0] < lineSmall[0]:
        ifGoldenCross = True

    for i in range (start, len(df) - 1):
        if lineBig[i] > lineSmall[i] and ifGoldenCross == True:
            if SMASmall == 5 and SMABig == 15:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="There was a death cross by SMA " + str(SMASmall) + " and SMA" + str(SMABig)
                    )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="There was a death cross by SMA" + str(SMASmall) + "and SMA" + str(SMABig),
                        possition = False,
                        stopLoss = (df.ClosePrice[i] / 100) * 101,
                        targetPrice = (df.ClosePrice[i] / 100) * 98,
                        openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
            elif SMASmall == 50 and SMABig == 100:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="There was a death cross by SMA " + str(SMASmall) + " and SMA" + str(SMABig)
                    )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="There was a death cross by SMA" + str(SMASmall) + "and SMA" + str(SMABig),
                        possition = False,
                        stopLoss = (df.ClosePrice[i] / 100) * 101,
                        targetPrice = (df.ClosePrice[i] / 100) * 98,
                        openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
            ifGoldenCross = False
        elif lineBig[i] < lineSmall[i] and ifGoldenCross == False:
            if SMASmall == 5 and SMABig == 15:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="There was a golden cross by SMA " + str(SMASmall) + " and SMA" + str(SMABig)
                    )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="There was a golden cross by SMA" + str(SMASmall) + "and SMA" + str(SMABig),
                        possition = True,
                        stopLoss = (df.ClosePrice[i] / 100) * 99,
                        targetPrice = (df.ClosePrice[i] / 100) * 102,
                        openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
            elif SMASmall == 50 and SMABig == 100:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="There was a golden cross by SMA " + str(SMASmall) + " and SMA" + str(SMABig)
                    )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="There was a golden cross by SMA" + str(SMASmall) + "and SMA" + str(SMABig),
                        possition = True,
                        stopLoss = (df.ClosePrice[i] / 100) * 99,
                        targetPrice = (df.ClosePrice[i] / 100) * 102,
                        openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
            ifGoldenCross = True

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

def BollingerBands(df, start):
    global lowVol
    for i in range (start, (len(df) - 1)):
        difference = df.UpperBB[i] - df.LowerBB[i]
        if df.ClosePrice[i] < df.LowerBB[i]:
            if lowVol:
                signal = Signal(
                    data=df.CloseTime[i],
                    information="Candle closed below the lower Bollinger Band at around " + str(df.CloseTime[i]) + "and market volatility is low",
                    possition = True,
                    stopLoss = (df.ClosePrice[i] / 100) * 99,
                    targetPrice = df.SMA20[i],
                    openPrice = df.ClosePrice[i]
                )
                db_session.add(signal)
                db_session.commit()
            else:
                signal = Signal(
                    data=df.CloseTime[i], 
                    information="Candle closed below the lower Bollinger Band at around " + str(df.CloseTime[i]) + "and market volatility is high",
                    possition = False,
                    stopLoss = df.SMA20[i],
                    targetPrice = (df.ClosePrice[i] / 100) * 98,
                    openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.commit()
        elif df.ClosePrice[i] > df.UpperBB[i]:
            if lowVol:
                signal = Signal(
                    data=df.CloseTime[i], 
                    information="Candle closed above the upper Bollinger Band at around " + str(df.CloseTime[i]) + "and market volatility is low",
                    possition = False,
                    stopLoss = (df.ClosePrice[i] / 100) * 101,
                    targetPrice = df.SMA20[i],
                    openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.commit()
            else:
                signal = Signal(
                    data=df.CloseTime[i],
                    information="Candle closed abobe the upper Bollinger Band at around " + str(df.CloseTime[i]) + "and market volatility is high",
                    possition = True,
                    stopLoss = df.SMA20[i],
                    targetPrice = (df.ClosePrice[i] / 100) * 102,
                    openPrice = df.ClosePrice[i]
                )
                db_session.add(signal)
                db_session.commit()
        


def isCloseToLines(df, start):
    lines = biggestTrendFibonacci(df)
    global isClose

    price = df.ClosePrice[start]

    currentInterval = 0
    for j in lines:
        if price > j:
            currentInterval += 1

    isBounce = 0

    for i in range (start, (len(df) - 1)):
        upLine = lines[currentInterval]
        downLine = lines[currentInterval - 1]
        delta = (upLine - downLine) * 5 / 100
        price = df.ClosePrice[i]
        
        if currentInterval < 1 or currentInterval > 5:
            print ("Error")
            return

        if price > (upLine - delta):
            if price < upLine + delta and isClose is False:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="Current price is close to the " + str(upLine) + " resistance zone"
                )
                db_session.add(notification)
                db_session.commit()
                isClose = True
                isBounce += 1
            elif price > upLine + delta:
                isClose = False
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="A candle closed above the " + str(upLine) + " resistance zone"
                )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="A candle closed above the " + str(upLine) + "resistance zone - the up trend should continue",
                        possition = True,
                        stopLoss = (df.ClosePrice[i] / 100) * 99,
                        targetPrice = (df.ClosePrice[i] / 100) * 102,
                        openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
                currentInterval += 1
                isBounce -= 1

        elif price < (downLine + delta):
            if price > downLine - delta and isClose is False:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="Current price is close to the " + str(downLine) + " support zone"
                )
                db_session.add(notification)
                db_session.commit()
                isClose = True
                isBounce -= 1
            elif price < downLine - delta:
                isClose = False
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="A candle closed below the " + str(downLine) + " support zone",
                )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="A candle closed below the " + str(downLine) + "support zone - the downtrend should continue",
                        possition = False,
                        stopLoss = (df.ClosePrice[i] / 100) * 101,
                        targetPrice = (df.ClosePrice[i] / 100) * 98,
                        openPrice = df.ClosePrice[i]
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
                currentInterval -= 1
                isBounce += 1

        else:
            if isClose:
                isClose = False
                if isBounce > 0:
                    notification = Notification(
                        data=df.CloseTime[i], 
                        information="The resistance zone was not breaked - price should be boncing down now",
                    )
                    signal = Signal(
                        data=df.CloseTime[i], 
                        information="The resistance zone was not breaked. Price should bounce down",
                        possition = False,
                        stopLoss = (df.ClosePrice[i] / 100) * 101,
                        targetPrice = (df.ClosePrice[i] / 100) * 98,
                        openPrice = df.ClosePrice[i]
                    )
                    db_session.add(signal)
                    db_session.add(notification)
                    db_session.commit()
                    isBounce = 0
                elif isBounce < 0:
                    notification = Notification(
                        data=df.CloseTime[i], 
                        information="The support zone was not breaked - price should be bouncing up now",
                    )
                    signal = Signal(
                        data=df.CloseTime[i], 
                        information="The support zone was not breaked. Price should bounce up",
                        possition = True,
                        stopLoss = (df.ClosePrice[i] / 100) * 99,
                        targetPrice = (df.ClosePrice[i] / 100) * 102,
                        openPrice = df.ClosePrice[i]
                    )
                    db_session.add(signal)
                    db_session.add(notification)
                    db_session.commit()
                    isBounce = 0
                else:
                    notification = Notification(
                        data=df.CloseTime[i], 
                        information="Price is not close to either of the zones anymore",
                    )
                    db_session.add(notification)
                    db_session.commit()


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

async def checkChanges(engine, candleSizeSeconds):
    while True:
        await asyncio.sleep(candleSizeSeconds)
        df = pd.read_sql('BTCUSDT', engine)
        df = df.iloc[:]
        findCross(df, len(df) - 2, False)
        isCloseToLines(df, len(df) - 2)
        BollingerBands(df, len(df) - 2)
        signals = Signal.query.all()
        for signal in signals:
            percentage = ((df[len(df) - 1].ClosePrice / signal.openPrice) - 1) / 100
            signal.percentage = percentage

            if signal.possition == True:
                if df[len(df) - 1].ClosePrice > signal.targetPrice:
                    print ("signal closed with a", percentage, "percent profit")
                    signal.closed = True
                elif df[len(df) - 1].ClosePrice < signal.stopLoss:
                    print ("signal closed with a", percentage, "percent loss")
                    signal.closed = True
            else:
                if df[len(df) - 1].ClosePrice < signal.targetPrice:
                    print ("signal closed with a", -percentage, "percent profit")
                    signal.closed = True
                elif df[len(df) - 1].ClosePrice > signal.stopLoss:
                    print ("signal closed with a", percentage, "percentage loss")
                    signal.closed = True
            db_session.commit()
        df = df.iloc[len(df) - 1:]
        print (df)
        print ("________________")

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    df = pd.read_sql('BTCUSDT', engine)
    df = df.iloc[:]
    #df = findEMA(df, [])
    #print (df)
    findCross(df, 0, False)
    BollingerBands(df, 0)
    candleSizeSeconds = int((df.OpenTime[1] - df.OpenTime[0]).total_seconds())
    isCloseToLines(df, 0)
    #displayCharts(df)
    print ("all fine!")
    loop = asyncio.get_event_loop()
    loop.create_task(checkChanges(engine, candleSizeSeconds))
    loop.run_forever()
    