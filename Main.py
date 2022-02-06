from binance.client import Client
from binance import BinanceSocketManager
import pandas as pd
import sqlalchemy


client = Client("CjhmrIu0k3VdrvML36fnYdx04kyA1u02QbJDUzirFfvHLx8wSEiiiRhRdrTzxika", "5faxSLXjUKKHsHT32kjkL78O75LzkeGI3c8Yp9awSQK7DMOlLoeMb990G1abbwrq")

engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')

df =pd.read_sql('BTCUSDT', engine)

print (df)