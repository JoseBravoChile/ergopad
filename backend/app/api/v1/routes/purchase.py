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

purchase_router = r = APIRouter()

#region BLOCKHEADER
"""
Purchase API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: allow purchase/redeem tokens locked by ergopad scripts
Contributor(s): https://github.com/Luivatra

Notes: 
"""
#endregion BLOCKHEADER

#region INIT
DEBUG = CFG.debug
st = time() # stopwatch

DATABASE = CFG.connectionString
DATEFORMAT = '%m/%d/%Y %H:%M'
NOW = int(time())

class TokenPurchase(BaseModel):
  wallet: str
  amount: float
  isToken: Optional[bool] = True
  currency: Optional[str] = 'sigusd'

# TODO: move to config
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

# purchase tokens
@r.post("/purchase/", name="blockchain:purchaseToken")
async def purchaseToken(tokenPurchase: TokenPurchase):  
  # early check
  try:
    nodeInfo = await getInfo()
    now = int(nodeInfo['currentTime_ms']/1000.0)
  except:
    now = int(time())
    pass
  logging.debug(now)
  if now < 1641229200:
    return {
      'status'  : 'waiting', 
      'now'     : now,
      'message' : 'token sale begins 1/3 @5p UTC',
    }

  # handle price exceptions
  tokenId = validCurrencies['ergopad'] #CFG.ergopadTokenId
  priceOverride = 5.0
  price = priceOverride
  try:
    sigusdCurrentPrice = await get_asset_current_price('sigusd') #Confusing naming, is this erg price in sigusd?
    if 'price' in sigusdCurrentPrice:
      price = sigusdCurrentPrice['price']
      if math.isnan(price): # NaN
        price = priceOverride
      if price < 1 or price > 1000: # OOS
        price = priceOverride

  except Exception as e:
    logging.error(f'{myself()}: {e}')
    logging.error('invalid price found for sigusd')
    pass

  # handle token params
  sigusdDecimals = 0
  ergopadDecimals = 0
  try:
    tokenDecimals = getTokenInfo(validCurrencies['sigusd'])
    logging.debug(tokenDecimals)
    if 'decimals' in tokenDecimals:
      sigusdDecimals = int(tokenDecimals['decimals'])
    tokenDecimals = getTokenInfo(validCurrencies['ergopad'])
    if 'decimals' in tokenDecimals:
      ergopadDecimals = int(tokenDecimals['decimals'])

  except Exception as e:
    logging.error(f'{myself()}: {e}')
    logging.error('invalid decimals found for sigusd')
    pass

  logging.info(f'decimals for sigusd: {sigusdDecimals}, ergopad: {ergopadDecimals}')
  ergopadDecimals = 10**ergopadDecimals
  sigusdDecimals = 10**sigusdDecimals

  # handle purchase
  try:
    buyerWallet        = Wallet(tokenPurchase.wallet)
    amount             = tokenPurchase.amount #Purchase amount in SigUSD

    isToken = True
    tokenName          = 'sigusd'
    if tokenPurchase.currency == 'erg':  
      isToken          = False
      tokenName        = None

    nergsPerErg        = 1000000000
    txFee_nerg         = int(.001*nergsPerErg)

    # if sending sigusd, assert(isToken)=True
    strategic2Sigusd   = .02 # strategic round .02 sigusd per token (50 strategic tokens per sigusd)
    tokenAmount        = int(amount/strategic2Sigusd)*ergopadDecimals 
    coinAmount_nerg    = int(amount/price*nergsPerErg) 
    sendAmount_nerg    = coinAmount_nerg+2*txFee_nerg
    if isToken:
      coinAmount_nerg  = txFee_nerg # min per box
      sendAmount_nerg  = 10000000 # coinAmount_nerg+txMin_nerg # +txFee_nerg

    logging.info(f'using {tokenName}, amount={tokenAmount/ergopadDecimals:.2f} at price={price} for {amount}sigusd')

    # check whitelist
    whitelist = {}
    remaining = {}

    try:
      with open(f'whitelist.csv') as f:
        wl = f.readlines()
        for w in wl: 
          whitelist[w.split(',')[2].rstrip()] = {
            'amount': float(w.split(',')[0]),
            # 'tokens': round(float(w.split(',')[1]))
          }
          # spentlist[w.split(',')[2].rstrip()] = 0

      with open(f'remaining.tsv') as f:
        for row in f.readlines():
          try:
            r = row.split('\t')
            remaining[r[0]] = {
              'total': float(r[1]),
              'spent': float(r[2]),
              'remaining': float(r[3]),
            }
          except:
            if row != None:
              logging.error(f'issue in remaining.tsv, line: {row}')
            pass

    except Exception as e:
      logging.error(f'ERR:{myself()}: reading whitelist ({e})')
      return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid whitelist/blacklist')

    # make sure buyer is whitelisted
    if buyerWallet.address not in whitelist:
      logging.debug(f'wallet not found in whitelist: {buyerWallet.address}')
      return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} invalid or not on whitelist')

    # make sure buyer remains under amount limit
    if amount > remaining[buyerWallet.address]['remaining']:
      logging.debug(f"amount ({amount}) exceeds whitelist amount: {remaining[buyerWallet.address]['remaining']}/{remaining[buyerWallet.address]['total']}, including already spent amount: {remaining[buyerWallet.address]['spent']}")
      return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} may only request up to {whitelist[buyerWallet.address]["sigusd"]} sigusd')

    # 1 outbox per vesting period to lock spending until vesting complete
    logging.info(f'wallet: ok\nwhitelist: ok\nergs: {coinAmount_nerg} at price {price}')

    # pay ergopad for tokens with coins or tokens
    # startWhen = {'erg': sendAmount_nerg}
    startWhen = {'erg': sendAmount_nerg}
    outBox = [{
        'address': nodeWallet.address, # nodeWallet.bs64(),
        'value': sendAmount_nerg # coinAmount_nerg
    }]
    if isToken:
      outBox[0]['assets'] = [{
            'tokenId': validCurrencies[tokenName], # sigusd
            'amount': int(amount*sigusdDecimals),
          }]
      startWhen[validCurrencies[tokenName]] = int(amount*sigusdDecimals)
    
    logging.info(f'startWhen: {startWhen}')

    # create outputs for each vesting period; add remainder to final output, if exists
    r4 = '0e'+hex(len(bytearray.fromhex(buyerWallet.ergoTree())))[2:]+buyerWallet.ergoTree() # convert to bytearray
    outBox.append({
      'address': buyerWallet.address,
      # 'value': txMin_nerg,
      'value': txFee_nerg,
      'registers': {
        'R4': r4
      },
      'assets': [{ 
        'tokenId': tokenId,
        'amount': int(tokenAmount) # full amount
      }]
    })

    logging.info(f'r4: {r4}')
    logging.info(f'wallets: {nodeWallet.address}, {buyerWallet.address}')
    logging.info(f"token: {tokenName}")

    # handle assembler
    params = {
      'nodeWallet': nodeWallet.address,
      'buyerWallet': buyerWallet.address,
      'timestamp': int(time()),      
      'purchaseToken': b64encode(validCurrencies['ergopad'].encode('utf-8').hex().encode('utf-8')).decode('utf-8'),
      'purchaseTokenAmount': tokenAmount
    }

    logging.info(f'params: {params}')

    params = {
      'nodeWallet': nodeWallet.address,
      'buyerWallet': buyerWallet.address,
      'saleTokenId': b64encode(bytes.fromhex(validCurrencies['ergopad'])).decode('utf-8'),
      'saleTokenAmount': tokenAmount,
      'timestamp': int(time()),      
    }
    if isToken:
      params['purchaseTokenId'] = b64encode(bytes.fromhex(validCurrencies['sigusd'])).decode('utf-8')
      params['purchaseTokenAmount'] = int(amount*sigusdDecimals)
    else:
      params['purchaseTokenId'] = ""
      params['purchaseTokenAmount'] = sendAmount_nerg # coinAmount_nerg

    logging.info(f'params: {params}')
    scPurchase = getErgoscript('directSale', params=params)

    logging.info(f'scPurchase: {scPurchase}')

    # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
    ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId=tokenId, nErgAmount=sendAmount_nerg, tokenAmount=tokenAmount)
    logging.info(f'build request')
    request = {
        'address': scPurchase,
        'returnTo': buyerWallet.address,
        'startWhen': startWhen,
        'txSpec': {
            'requests': outBox,
            'fee': txFee_nerg,
            'inputs': ['$userIns']+list(ergopadTokenBoxes.keys()),
            'dataInputs': [],
        },
    }
    
    # don't bonk if can't jsonify request
    try: logging.info(f'request: {json.dumps(request)}')
    except: pass

    # logging.info(f'build request: {request}')
    # logging.info(f'\n::REQUEST::::::::::::::::::\n{json.dumps(request)}\n::REQUEST::::::::::::::::::\n')

    # make async request to assembler
    res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)    
    logging.debug(res)
    id = res.json()['id']
    fin = requests.get(f'{CFG.assembler}/result/{id}')
    logging.info({'status': 'success', 'fin': fin.json(), 'followId': id})

    # save buyer info
    with open(f'blacklist.tsv', 'a') as f:
      # buyer, timestamp, sigusd, uuid
      f.write('\t'.join([buyerWallet.address, str(time()), str(amount), str(id)])+'\n')

    await handleAllowance()

    logging.debug(f'::TOOK {time()-st:.2f}s')
    if isToken:
      message = f'send {sendAmount_nerg/nergsPerErg} ergs and {amount} sigusd to {scPurchase}'
    else:
      message = f'send {sendAmount_nerg/nergsPerErg} ergs to {scPurchase}'
    return({
        'status'        : 'success', 
        'message'       : message,
        'total'         : sendAmount_nerg/nergsPerErg,
        # 'coins'         : coinAmount_nerg/nergsPerErg,
        # 'boxes'         : txBoxTotal_nerg/nergsPerErg,
        # 'fees'          : txFee_nerg/nergsPerErg,
        'assembler'     : json.dumps(fin.json()),
        'smartContract' : scPurchase, 
        'request'       : json.dumps(request),
    })

  except Exception as e:
    logging.error(f'ERR:{myself()}: building request ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'building request')

### MAIN
if __name__ == '__main__':
    print('API routes: ...')
