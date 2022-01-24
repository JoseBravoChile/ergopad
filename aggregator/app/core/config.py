import os

from sqlalchemy import create_engine

PROJECT_NAME = "satellite"

# POWERNAP = int(os.getenv('POWERNAP')) or 60 # seconds
POWERNAP = 60  # for main and using modulus on 1 minute, this should be 60s
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASS = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DBNM = os.getenv('POSTGRES_DBNM')

# API
APIKEYS = {
    'coinex': {
        'ACCESS_ID': os.getenv('COINEX_ACCESS_ID'),
        'SECRET_KEY': os.getenv('COINEX_SECRET_KEY'),
    }
}

# DATABASE CONNECTION
db = create_engine(
    f'postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@postgres:{POSTGRES_PORT}/{POSTGRES_DBNM}')

# CONFIG
TIMEFRAMES = ['1m', '5m', '1d', '1w']
# import these symbols
# TODO: convert to dict {'exchange': ['coin1', 'coin2']}, or move to config file and include additional infor like exchange api keys, etc..
SYMBOLS = ['ERG/USDT', 'ETH/USDT', 'BTC/USDT']
