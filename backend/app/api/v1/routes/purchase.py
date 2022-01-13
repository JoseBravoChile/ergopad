import requests, json, os
import math
import uuid

from starlette.responses import JSONResponse 
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time, ctime
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode
from ergo.updateAllowance import handleAllowance
from ergo.util import encodeLong, encodeString
from config import Config, Network # api specific config
CFG = Config[Network]

blockchain_router = r = APIRouter()

#region BLOCKHEADER
"""
Purchase API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: allow purchase/redeem tokens locked by ergopad scripts
Contributor(s): https://github.com/Luivatra

Notes: 
- 
"""
#endregion BLOCKHEADER

#region INIT
DEBUG = CFG.debug
st = time() # stopwatch

class TokenPurchase(BaseModel):
  wallet: str
  amount: float
  isToken: Optional[bool] = True
  currency: Optional[str] = 'sigusd'

try:
  headers            = {'Content-Type': 'application/json'}
  tokenInfo          = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')

  if Network == 'testnet':
    validCurrencies    = {
      'sigusd'   : '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
      'ergopad'  : '5ff2d1cc22ebf959b1cc65453e4ee225b0fdaf4c38a12e3b4ba32ff769bed70f', # 
    }
    nodeWallet         = Wallet('3WxMzA9TwMYh9M5ivSfHi5VqUDhUS6nX4B8ZQNqGLupZqZfivmUw') # contains tokens
    buyerWallet        = Wallet('3WzKuUxmG7HtfmZNxxHw3ArPzsZZR96yrNkTLq4i1qFwVqBXAU8M') # simulate buyer

  # mainnet
  else:
    validCurrencies    = {
      'ergopad'  : '60def1ed45ffc6493c8c6a576c7a23818b6b2dfc4ff4967e9867e3795886c437', # official
      'sigusd'   : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD (SigmaUSD - V2)
    }
    nodeWallet         = Wallet('9gibNzudNny7MtB725qGM3Pqftho1SMpQJ2GYLYRDDAftMaC285') # contains ergopad tokens (xerg10M)
    buyerWallet        = Wallet('9iLSsvi2zobapQmi7tXVK4mnrbQwpK3oTfPcCpF9n7J2DQVpxq2') # simulate buyer / seed tokens

  CFG.ergopadTokenId = validCurrencies['ergopad'] 
  CFG.sigusdTokenId  = validCurrencies['sigusd']

except Exception as e:
  logging.error(f'Init {e}')
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING
