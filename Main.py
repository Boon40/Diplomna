from asyncio.tasks import sleep
from binance.client import Client
from binance import BinanceSocketManager
import asyncio
import pandas as pd
import sqlalchemy


client = Client(#key, secret key)
bsm = BinanceSocketManager(client)

engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')

df = pd.read_sql('BTCUSDT', engine)

print (df)