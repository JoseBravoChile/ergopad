import requests, json, os

from sqlalchemy import create_engine
from starlette.responses import JSONResponse
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from base64 import b64encode
from ergo.util import encodeLong, encodeString

from config import Config, Network # api specific config
CFG = Config[Network]

dapp_router = r = APIRouter()

#region BLOCKHEADER
"""
Blockchain API
---------
Created: sigma@ergopad.io
On: 20220210
Purpose: integrate api with wallets (i.e. nautulis)
Contributor(s): https://github.com/Luivatra

Notes:
"""
#endregion BLOCKHEADER

#region INIT
DEBUG = CFG.debug
st = time() # stopwatch

currency = 'usd' # TODO: store with user
total_sigrsv = 10**11+.01 # initial amount SigRSV
default_rsv_price = 10**6 # lower bound/default SigRSV value
nerg2erg = 10**9 # 1e9 satoshis/kushtis in 1 erg
ergo_watch_api = CFG.ergoWatch
oracle_pool_url = CFG.oraclePool
coingecko_url = CFG.coinGecko
exchange = 'coinex'
symbol = 'ERG/USDT'

con = create_engine(CFG.connectionString)
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region ROUTES
#endregion ROUTES
