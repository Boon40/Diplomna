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

def getHistoricalData4Hours(token_name):
    client = Client("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(client)
    socket = bsm.trade_socket(token_name)
    firstRun = True
    for currKline in client._historical_klines_generator(token_name, client.KLINE_INTERVAL_1MINUTE, str(datetime.now() - relativedelta(hours=5))):
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

async def getCurrentData4Hours(token_name, df):
    asyncClient = await AsyncClient.create("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(asyncClient)
    socket = bsm.trade_socket(token_name)

    await asyncio.sleep(60)
    while True:
        dataSize = len(df)
        SMA5, SMA15, SMA50, SMA100 = 0, 0, 0, 0

        for i in range (dataSize, dataSize - 100):
            if i > dataSize - 5:
                SMA5 += df.ClosePrise[i]
            if i > dataSize - 15:
                    SMA15 += df.ClosePrise[i]
            if i > dataSize - 50:
                SMA50 += df.ClosePrise[i]
            SMA100 += df.ClosePrise[i]
        SMA5 /= 5
        SMA15 /= 15
        SMA50 /= 50
        SMA100 /= 100

        msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_1MINUTE, limit=1)
        frame = createFrame(msg[0], [SMA5, SMA15, SMA50, SMA100])
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print(frame)
        await asyncio.sleep(60)

def getHistoricalData1Day(token_name):
    client = Client("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(client)
    socket = bsm.trade_socket(token_name)
    for currKline in client._historical_klines_generator(token_name, client.KLINE_INTERVAL_1DAY, str(datetime.now() - relativedelta(years=1))):
        frame = createFrame(currKline)
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print (frame)

async def getCurrentData1Day(token_name):
    asyncClient = await AsyncClient.create("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(asyncClient)
    socket = bsm.trade_socket(token_name)

    await asyncio.sleep(86400)
    while True:
        msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_1DAY, limit=1)
        frame = createFrame(msg[0])
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print(frame)
        await asyncio.sleep(86400)

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
    getHistoricalData4Hours('BTCUSDT')
    df = pd.read_sql('BTCUSDT', engine)
    df = df.iloc[:]
    print (df)

    loop = asyncio.get_event_loop()
    loop.create_task(getCurrentData4Hours('BTCUSDT', df))
    #loop.create_task(getCurrentData1Day('BTCUSDT'))
    loop.run_forever()