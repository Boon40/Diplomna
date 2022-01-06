from asyncio.tasks import sleep
from binance.client import Client
from binance import BinanceSocketManager
import asyncio
import pandas as pd
import sqlalchemy
import time


client = Client(#key, secret key)
bsm = BinanceSocketManager(client)

async def print_info(token_name):
    socket = bsm.trade_socket(token_name)
    while True:
        await socket.__aenter__()
        msg = await socket.recv()
        frame = createFrame (msg)
        frame.to_sql('BTCUSDT', engine, if_exists='append', index=False)
        print(frame)

def createFrame(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:,['s','E','p']]
    df.columns = ['symbol','Time','Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:///BTCUSDTstream.db')
    loop = asyncio.get_event_loop()
    loop.create_task(print_info('BTCUSDT'))
    loop.run_forever()
