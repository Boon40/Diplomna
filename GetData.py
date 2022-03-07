from multiprocessing.connection import Client
from sqlite3 import TimestampFromTicks
from time import sleep
from binance import AsyncClient
from binance import Client
from binance import BinanceSocketManager
import asyncio
from matplotlib.pyplot import get
import pandas as pd
import sqlalchemy
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')

def getHistoricalData(token_name, candleSize):
    client = Client("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(client)
    socket = bsm.trade_socket(token_name)
    firstRun = True
    pastTime = relativedelta(hours=8)
    if candleSize == '1M':
        candleSize = client.KLINE_INTERVAL_1MINUTE
    elif candleSize == '15M':
        candleSize = client.KLINE_INTERVAL_15MINUTE
        pastTime = relativedelta(days=5)
    elif candleSize == '1H':
        candleSize = client.KLINE_INTERVAL_1HOUR
        pastTime = relativedelta(days=15)
    elif candleSize == '4H':
        candleSize = client.KLINE_INTERVAL_4HOUR
        pastTime = relativedelta(days=70)
    elif candleSize == '8H':
        candleSize = client.KLINE_INTERVAL_8HOUR
        pastTime = relativedelta(days=140)
    elif candleSize == '12H':
        candleSize = client.KLINE_INTERVAL_12HOUR
        pastTime = relativedelta(days=210)
    elif candleSize == '1D':
        candleSize = client.KLINE_INTERVAL_1DAY
        pastTime = relativedelta(years=1)
    else:
        print ("That's an invalid candle size!")
        return
    for currKline in client._historical_klines_generator(token_name, candleSize, str(datetime.now() - pastTime)):
        SMA5, SMA15, SMA50, SMA100 = 0, 0, 0, 0
        if not firstRun:
            df = pd.read_sql('BTCUSDT', engine)
            size = len(df) - 1
            if size > 5:
                for i in range (size - 5, size):
                    SMA5 += df.ClosePrice[i]
                SMA5 /= 5

            if size > 15:
                for i in range (size - 15, size):
                    SMA15 += df.ClosePrice[i]
                SMA15 /= 15

            if size > 50:
                for i in range (size - 50, size):
                    SMA50 += df.ClosePrice[i]
                SMA50 /= 50

            if size > 100:
                for i in range (size - 100, size):
                    SMA100 += df.ClosePrice[i]
                SMA100 /= 100
        firstRun = False
        frame = createFrame(currKline, [SMA5, SMA15, SMA50, SMA100])
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print (frame)

async def getCurrentData(token_name, engine, candleSize):
    asyncClient = await AsyncClient.create("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(asyncClient)
    socket = bsm.trade_socket(token_name)
    if candleSize == '1M':
        await asyncio.sleep(60)
    elif candleSize == '15M':
        await asyncio.sleep(900)
    elif candleSize == '1H':
        await asyncio.sleep(3600)
    elif candleSize == '4H':
        await asyncio.sleep(14400)
    elif candleSize == '8H':
        await asyncio.sleep(28800)
    elif candleSize == '12H':
        await asyncio.sleep(43200)
    elif candleSize == '1D':
        await asyncio.sleep(86400)
    else:
        print ("That's an invalid candle size!")
        return
    while True:
        df = pd.read_sql('BTCUSDT', engine)
        df = df.iloc[:]
        dataSize = len(df) - 1
        if dataSize < 150:
            print ("Not enough data to calculate the simple moving averages")
            return
        SMA5, SMA15, SMA50, SMA100 = 0, 0, 0, 0

        #Ribcho range step = -1 (default 1)
        for i in range (dataSize, dataSize - 100, -1):
            if i > dataSize - 5:
                SMA5 += df.ClosePrice[i]
            if i > dataSize - 15:
                    SMA15 += df.ClosePrice[i]
            if i > dataSize - 50:
                SMA50 += df.ClosePrice[i]
            SMA100 += df.ClosePrice[i] 
        SMA5 /= 5
        SMA15 /= 15
        SMA50 /= 50
        SMA100 /= 100
        if candleSize == '1M':
            msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_1MINUTE, limit=1)
            await asyncio.sleep(60)
        elif candleSize == '15M':
            msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_15MINUTE, limit=1)
            await asyncio.sleep(900)
        elif candleSize == '1H':
            msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_1HOUR, limit=1)
            await asyncio.sleep(3600)
        elif candleSize == '4H':
            msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_4HOUR, limit=1)
            await asyncio.sleep(14400)
        elif candleSize == '8H':
            msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_8HOUR, limit=1)
            await asyncio.sleep(28800)
        elif candleSize == '12H':
            msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_12HOUR, limit=1)
            await asyncio.sleep(43200)
        elif candleSize == '1D':
            msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_1DAY, limit=1)
            await asyncio.sleep(86400)
        frame = createFrame(msg[0], [SMA5, SMA15, SMA50, SMA100])
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print(frame)

def createFrame(msg, SMAs):
    values = []
    titles = []
    if len(SMAs) > 0:
        values = ["BTCUSDT", msg[0], msg[1], msg[2], msg[3], msg[4], msg[6], SMAs[0], SMAs[1], SMAs[2], SMAs[3]]
        titles = ["Symbol", "OpenTime", "OpenPrice", "High", "Low", "ClosePrice", "CloseTime", "SMA5", "SMA15", "SMA50", "SMA100"]
    else:
        values = ["BTCUSDT", msg[0], msg[1], msg[2], msg[3], msg[4], msg[6]]
        titles = ["Symbol", "OpenTime", "OpenPrice", "High", "Low", "ClosePrice", "CloseTime"]
    info = dict(zip(titles, values))
    frame = pd.DataFrame([info])
    if len(SMAs) > 0:
        frame = frame.loc[:,["Symbol", "OpenTime", "OpenPrice", "High", "Low", "ClosePrice", "CloseTime", "SMA5", "SMA15", "SMA50", "SMA100"]]
        frame.columns = ['Symbol', 'OpenTime', 'OpenPrice', 'High', 'Low', 'ClosePrice', 'CloseTime', 'SMA5', 'SMA15', 'SMA50', 'SMA100']
    else:
        frame = frame.loc[:,["Symbol", "OpenTime", "OpenPrice", "High", "Low", "ClosePrice", "CloseTime"]]
        frame.columns = ['Symbol', 'OpenTime', 'OpenPrice', 'High', 'Low', 'ClosePrice', 'CloseTime']
    frame.OpenTime = pd.to_datetime(frame.OpenTime, unit='ms')
    frame.OpenPrice = frame.OpenPrice.astype(float)
    frame.High = frame.High.astype(float)
    frame.Low = frame.Low.astype(float)
    frame.ClosePrice = frame.ClosePrice.astype(float)
    frame.CloseTime = pd.to_datetime(frame.CloseTime, unit='ms')
    if len(SMAs) > 0:
        frame.SMA5 = frame.SMA5.astype(float)
        frame.SMA15 = frame.SMA15.astype(float)
        frame.SMA50 = frame.SMA50.astype(float)
        frame.SMA100 = frame.SMA100.astype(float)
    return frame

def findSMA(df, periods, SMAs = []):
    title = "SMA" + str(periods)

    if len(df) == len(SMAs):
        df[title] = SMAs
        return (df)

    if len(df) < (periods * 1.5):
        print ("not enough df to analyse!")
        return

    while (len(SMAs) < periods):
        SMAs.append(0)

    PricesSum = 0
    for i in range (len(SMAs) - periods, (len(SMAs))):
        PricesSum += df.ClosePrice[i]
    PricesSum /= periods
    SMAs.append(PricesSum)
    return findSMA(df, periods, SMAs)

if __name__ == "__main__":
    #getHistoricalData1Day('BTCUSDT')
    getHistoricalData('BTCUSDT', "15M")
    df = pd.read_sql('BTCUSDT', engine)
    df = df.iloc[:]
    print (df)

    loop = asyncio.get_event_loop()
    loop.create_task(getCurrentData('BTCUSDT', engine, "15M"))
    #loop.create_task(getCurrentData1Day('BTCUSDT'))
    loop.run_forever()