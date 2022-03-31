from audioop import add
from curses import def_shell_mode
from re import I
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
firstRun = True
isClose = False
bbup = False
bbdown = False


def findLowestPrice(amount, df):
    lowest = df.ClosePrice[0]
    index = 0
    for i in range (0, amount):
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

def findCross(df, start):
    lineSmall = df.SMA50
    lineBig = df.SMA100
    SMASmall = 50
    SMABig = 100
    global ifGoldenCross
    global firstRun
    if lineBig[0] < lineSmall[0]:
        ifGoldenCross = True

    for i in range (start, len(df) - 1):
        if lineBig[i] > lineSmall[i] and ifGoldenCross == True:
            if not firstRun:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="There was a death cross by SMA " + str(SMASmall) + " and SMA" + str(SMABig)
                    )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="There was a death cross by SMA" + str(SMASmall) + "and SMA" + str(SMABig),
                        possition = False,
                        stopLoss = round(df.ClosePrice[i] * 1.01, 2),
                        targetPrice = round(df.ClosePrice[i] * 0.98, 2),
                        openPrice = round(df.ClosePrice[i], 2)
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
            firstRun = False
            ifGoldenCross = False
        elif lineBig[i] < lineSmall[i] and ifGoldenCross == False:
            if not firstRun:
                notification = Notification(
                    data=df.CloseTime[i], 
                    information="There was a golden cross by SMA " + str(SMASmall) + " and SMA" + str(SMABig)
                    )
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="There was a golden cross by SMA" + str(SMASmall) + "and SMA" + str(SMABig),
                        possition = True,
                        stopLoss = round(df.ClosePrice[i] * 0.99, 2),
                        targetPrice = round(df.ClosePrice[i] * 1.02, 2),
                        openPrice = round(df.ClosePrice[i])
                    )
                db_session.add(signal)
                db_session.add(notification)
                db_session.commit()
            firstRun = False
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


def BollingerBands(df, start):
    global bbup
    global bbdown
    for i in range (start, (len(df) - 1)):
        if df.ClosePrice[i] < df.LowerBB[i] and not bbdown:
            signal = Signal(
                data=df.CloseTime[i],
                information="Candle closed below the lower Bollinger Band at around " + str(df.CloseTime[i]),
                possition = True,
                stopLoss = round(df.ClosePrice[i] * 0.99, 2),
                targetPrice = round(df.SMA20[i], 2),
                openPrice = round(df.ClosePrice[i]),
                targetSMA = True
            )
            db_session.add(signal)
            db_session.commit()
            bbdown = True
        elif df.ClosePrice[i] > df.UpperBB[i] and not bbup:
            signal = Signal(
                data=df.CloseTime[i], 
                information="Candle closed above the upper Bollinger Band at around " + str(df.CloseTime[i]),
                possition = False,
                stopLoss = round(df.ClosePrice[i] * 1.01, 2),
                targetPrice = round(df.SMA20[i], 2),
                openPrice = round(df.ClosePrice[i], 2),
                targetSMA = True
                )
            db_session.add(signal)
            db_session.commit()
            bbup = True

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
                    information="Current price is close to the " + str(round(upLine, 2)) + " resistance zone"
                )
                db_session.add(notification)
                db_session.commit()
                isClose = True
                isBounce += 1
            elif price > upLine + delta:
                isClose = False
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="A candle closed above the " + str(round(upLine, 2)) + "resistance zone - the up trend should continue",
                        possition = True,
                        stopLoss = round(df.ClosePrice[i] * 0.99, 2),
                        targetPrice = round(df.ClosePrice[i] * 1.02, 2),
                        openPrice = round(df.ClosePrice[i], 2)
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
                    information="Current price is close to the " + str(round(downLine, 2)) + " support zone"
                )
                db_session.add(notification)
                db_session.commit()
                isClose = True
                isBounce -= 1
            elif price < downLine - delta:
                isClose = False
                signal = Signal(
                        data=df.CloseTime[i], 
                        information="A candle closed below the " + str(round(downLine, 2)) + "support zone - the downtrend should continue",
                        possition = False,
                        stopLoss = round(df.ClosePrice[i] * 1.01, 2),
                        targetPrice = round(df.ClosePrice[i] * 0.98, 2),
                        openPrice = round(df.ClosePrice[i], 2)
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
                    signal = Signal(
                        data=df.CloseTime[i], 
                        information="The resistance zone was not breaked. Price should bounce down",
                        possition = False,
                        stopLoss = round(df.ClosePrice[i] * 1.02, 2),
                        targetPrice = round(df.ClosePrice[i] * 0.98, 2),
                        openPrice = round(df.ClosePrice[i], 2)
                    )
                    db_session.add(signal)
                    db_session.add(notification)
                    db_session.commit()
                    isBounce = 0
                elif isBounce < 0:
                    signal = Signal(
                        data=df.CloseTime[i], 
                        information="The support zone was not breaked. Price should bounce up",
                        possition = True,
                        stopLoss = round(df.ClosePrice[i] * 0.99, 2),
                        targetPrice = round(df.ClosePrice[i] * 1.02, 2),
                        openPrice = round(df.ClosePrice[i], 2)
                    )
                    db_session.add(signal)
                    db_session.add(notification)
                    db_session.commit()
                    isBounce = 0

def checkSignals(df):
    global bbup
    global bbdown
    for i in range (1, Signal.query.count() + 1):
        signal = Signal.query.filter_by(id = i).first()
        percentage = round((((df.ClosePrice[len(df) - 1] - signal.openPrice) * 100) / signal.openPrice), 2)

        if signal.closed:
            continue
        if signal.targetSMA:
            signal.targetPrice = round(df.SMA20[len(df) - 1], 2)
        if signal.possition:
            signal.percentage = percentage
            if df.ClosePrice[len(df) - 1] > signal.targetPrice or df.ClosePrice[len(df) - 1] < signal.stopLoss:
                signal.closed = True
                signal.closeDate = df.CloseTime[len(df) - 1]
                if bbdown:
                    bbdown = False
        else:
            signal.percentage = -percentage
            if df.ClosePrice[len(df) - 1] < signal.targetPrice or df.ClosePrice[len(df) - 1] > signal.stopLoss:
                signal.closed = True
                signal.closeDate = df.CloseTime[len(df) - 1]
                if bbup:
                    bbup = False
            
        new_signal = signal
        db_session.delete(signal)
        db_session.add(new_signal)
        db_session.commit()

async def checkChanges(engine, candleSizeSeconds):
    while True:
        await asyncio.sleep(candleSizeSeconds)
        df = pd.read_sql('BTCUSDT', engine)
        df = df.iloc[:]
        findCross(df, len(df) - 2)
        isCloseToLines(df, len(df) - 2)
        BollingerBands(df, len(df) - 2)
        checkSignals(df)
        df = df.iloc[len(df) - 1:]

if __name__ == "__main__":
    Signal.query.delete()
    Notification.query.delete()
    db_session.commit()
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    df = pd.read_sql('BTCUSDT', engine)
    df = df.iloc[:]
    findCross(df, len(df) - 10)
    candleSizeSeconds = int((df.OpenTime[1] - df.OpenTime[0]).total_seconds())
    isCloseToLines(df, len(df) - 10)
    checkSignals(df)
    print ("Done!")
    loop = asyncio.get_event_loop()
    loop.create_task(checkChanges(engine, candleSizeSeconds))
    loop.run_forever()
    