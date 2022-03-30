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
                        stopLoss = round(df.ClosePrice[i] * 1.01, 2),
                        targetPrice = round(df.ClosePrice[i] * 0.98, 2),
                        openPrice = round(df.ClosePrice[i], 2)
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
                        stopLoss = round(df.ClosePrice[i] * 1.01, 2),
                        targetPrice = round(df.ClosePrice[i] * 0.98, 2),
                        openPrice = round(df.ClosePrice[i], 2)
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
                        stopLoss = round(df.ClosePrice[i] * 0.99, 2),
                        targetPrice = round(df.ClosePrice[i] * 1.02, 2),
                        openPrice = round(df.ClosePrice[i])
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
                        stopLoss = round(df.ClosePrice[i] * 0.99, 2),
                        targetPrice = round(df.ClosePrice[i] * 1.02, 2),
                        openPrice = round(df.ClosePrice[i])
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


def BollingerBands(df, start):
    for i in range (start, (len(df) - 1)):
        if df.ClosePrice[i] < df.LowerBB[i]:
            signal = Signal(
                data=df.CloseTime[i],
                information="Candle closed below the lower Bollinger Band at around " + str(df.CloseTime[i]),
                possition = True,
                stopLoss = round(df.ClosePrice[i] * 0.99, 2),
                targetPrice = round(df.SMA20[i], 2),
                openPrice = round(df.ClosePrice[i]),
                targetSMA = True
            )
            print ("SMA20:", round(df.SMA20[i], 2))
            db_session.add(signal)
            db_session.commit()
        elif df.ClosePrice[i] > df.UpperBB[i]:
            signal = Signal(
                data=df.CloseTime[i], 
                information="Candle closed above the upper Bollinger Band at around " + str(df.CloseTime[i]),
                possition = False,
                stopLoss = round(df.ClosePrice[i] * 1.01, 2),
                targetPrice = round(df.SMA20[i], 2),
                openPrice = round(df.ClosePrice[i], 2),
                targetSMA = True
                )
            print ("SMA20:", round(df.SMA20[i], 2))
            db_session.add(signal)
            db_session.commit()

def isCloseToLines(df, start):
    lines = biggestTrendFibonacci(df)
    global isClose

    price = df.ClosePrice[start]
    print (lines, "price:", price)
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
                    notification = Notification(
                        data=df.CloseTime[i], 
                        information="The resistance zone was not breaked - price should be boncing down now",
                    )
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
                    notification = Notification(
                        data=df.CloseTime[i], 
                        information="The support zone was not breaked - price should be bouncing up now",
                    )
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
                else:
                    notification = Notification(
                        data=df.CloseTime[i], 
                        information="Price is not close to either of the zones anymore",
                    )
                    db_session.add(notification)
                    db_session.commit()

def checkSignals(df):
    for i in range (1, Signal.query.count() + 1):
        signal = Signal.query.filter_by(id = i).first()
        percentage = round((((df.ClosePrice[len(df) - 1] - signal.openPrice) * 100) / signal.openPrice), 2)
        print (percentage)

        if signal.closed:
            continue
        if signal.targetSMA:
            signal.targetPrice = round(df.SMA20[len(df) - 1], 2)
        if signal.possition:
            signal.percentage = percentage
            if df.ClosePrice[len(df) - 1] > signal.targetPrice or df.ClosePrice[len(df) - 1] < signal.stopLoss:
                signal.closed = True
                signal.closeDate = df.CloseTime[len(df) - 1]
        else:
            signal.percentage = -percentage
            if df.ClosePrice[len(df) - 1] < signal.targetPrice or df.ClosePrice[len(df) - 1] > signal.stopLoss:
                signal.closed = True
                signal.closeDate = df.CloseTime[len(df) - 1]
            
        new_signal = signal
        db_session.delete(signal)
        db_session.add(new_signal)
        db_session.commit()

async def checkChanges(engine, candleSizeSeconds):
    while True:
        await asyncio.sleep(candleSizeSeconds)
        df = pd.read_sql('BTCUSDT', engine)
        df = df.iloc[:]
        findCross(df, len(df) - 2, False)
        isCloseToLines(df, len(df) - 2)
        BollingerBands(df, len(df) - 2)
        checkSignals(df)
        df = df.iloc[len(df) - 1:]
        print (df)
        print ("________________")

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    df = pd.read_sql('BTCUSDT', engine)
    df = df.iloc[:]
    #df = findEMA(df, [])
    #print (df)
    #findCross(df, 0, False)
    #BollingerBands(df, 0)
    candleSizeSeconds = int((df.OpenTime[1] - df.OpenTime[0]).total_seconds())
    #isCloseToLines(df, 0)
    print ("all fine!")
    loop = asyncio.get_event_loop()
    loop.create_task(checkChanges(engine, candleSizeSeconds))
    loop.run_forever()
    