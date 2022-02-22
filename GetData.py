from multiprocessing.connection import Client
from sqlite3 import TimestampFromTicks
from binance import AsyncClient
from binance import Client
from binance import BinanceSocketManager
import asyncio
from matplotlib.pyplot import get
import pandas as pd
import sqlalchemy
import json

async def getData(token_name):
    client = await AsyncClient.create("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(client)
    socket = bsm.trade_socket(token_name)

    while True:
        msg = await client.get_klines(symbol='BTCUSDT', interval=client.KLINE_INTERVAL_1MINUTE, limit=1)
        frame = createFrame(msg)
        frame.to_sql('BTCUSDT', engine, if_exists='append', index=False)
        print(frame)
        await asyncio.sleep(60)

def getHistoricalCandles(token_name):
    client = Client("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")
    bsm = BinanceSocketManager(client)
    socket = bsm.trade_socket(token_name)

    for currKline in client._historical_klines_generator(token_name, client.KLINE_INTERVAL_8HOUR, "15 Aug, 2021"):
        frame = createFrame(currKline)
        frame.to_sql('BTCUSDT', engine, if_exists='append', index=False)
        print (frame)


def createFrame(msg):
    values = ["BTCUSDT", msg[0], msg[1], msg[2], msg[3], msg[4], msg[6]]
    titles = ["symbol", "OT", "OP", "H", "L", "CP", "CT", "PD"]
    info = dict(zip(titles, values))
    frame = pd.DataFrame([info])
    frame = frame.loc[:,["symbol", "OT", "OP", "H", "L", "CP", "CT"]]
    frame.columns = ['symbol', 'OT', 'OP', 'H', 'L', 'CP', 'CT']
    frame.OT = pd.to_datetime(frame.OT, unit='ms')
    frame.OP = frame.OP.astype(float)
    frame.H = frame.H.astype(float)
    frame.L = frame.L.astype(float)
    frame.CP = frame.CP.astype(float)
    frame.CT = pd.to_datetime(frame.CT, unit='ms')
    return frame

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    getHistoricalCandles('BTCUSDT')
    #loop = asyncio.get_event_loop()
    #loop.create_task(getData('BTCUSDT'))
    #loop.run_forever()
