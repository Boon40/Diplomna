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

def getHistoricalData4Hours(token_name):
    client = Client("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(client)
    socket = bsm.trade_socket(token_name)
    for currKline in client._historical_klines_generator(token_name, client.KLINE_INTERVAL_1MINUTE, str(datetime.now() - relativedelta(hours=8))):
        frame = createFrame(currKline, "1M")
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print (frame)

async def getCurrentData4Hours(token_name):
    asyncClient = await AsyncClient.create("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(asyncClient)
    socket = bsm.trade_socket(token_name)

    await asyncio.sleep(60)
    while True:
        msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_1MINUTE, limit=1)
        frame = createFrame(msg[0], "1M")
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print(frame)
        await asyncio.sleep(60)

def getHistoricalData1Day(token_name):
    client = Client("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(client)
    socket = bsm.trade_socket(token_name)
    for currKline in client._historical_klines_generator(token_name, client.KLINE_INTERVAL_1DAY, str(datetime.now() - relativedelta(years=1))):
        frame = createFrame(currKline, "1D")
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print (frame)

async def getCurrentData1Day(token_name):
    asyncClient = await AsyncClient.create("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(asyncClient)
    socket = bsm.trade_socket(token_name)

    await asyncio.sleep(86400)
    while True:
        msg = await asyncClient.get_klines(symbol=token_name, interval=asyncClient.KLINE_INTERVAL_1DAY, limit=1)
        frame = createFrame(msg[0], "1D")
        frame.to_sql(token_name, engine, if_exists='append', index=False)
        print(frame)
        await asyncio.sleep(86400)

def createFrame(msg, candleSize):
    values = ["BTCUSDT", msg[0], msg[1], msg[2], msg[3], msg[4], msg[6], candleSize]
    titles = ["Symbol", "OpenTime", "OpenPrice", "High", "Low", "ClosePrice", "CloseTime", "CandleSize"]
    info = dict(zip(titles, values))
    frame = pd.DataFrame([info])
    frame = frame.loc[:,["Symbol", "OpenTime", "OpenPrice", "High", "Low", "ClosePrice", "CloseTime", "CandleSize"]]
    frame.columns = ['Symbol', 'OpenTime', 'OpenPrice', 'High', 'Low', 'ClosePrice', 'CloseTime', 'CandleSize']
    frame.OpenTime = pd.to_datetime(frame.OpenTime, unit='ms')
    frame.OpenPrice = frame.OpenPrice.astype(float)
    frame.High = frame.High.astype(float)
    frame.Low = frame.Low.astype(float)
    frame.ClosePrice = frame.ClosePrice.astype(float)
    frame.CloseTime = pd.to_datetime(frame.CloseTime, unit='ms')
    frame.CandleSize = frame.CandleSize.astype(str)
    return frame

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    getHistoricalData1Day('BTCUSDT')
    #getHistoricalData4Hours('BTCUSDT')
    loop = asyncio.get_event_loop()
    #loop.create_task(getCurrentData4Hours('BTCUSDT'))
    loop.create_task(getCurrentData1Day('BTCUSDT'))
    loop.run_forever()
