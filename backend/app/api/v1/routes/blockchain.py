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
Blockchain API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211009
Purpose: allow purchase/redeem tokens locked by ergopad scripts
Contributor(s): https://github.com/Luivatra

Notes: 
- /utils/ergoTreeToAddress/{ergoTreeHex} can convert from ergotree (in R4)

** PREPARE FOR PROD
!! figure out proper payment amounts to send !!

Later
- build route that tells someone how much they have locked
?? log to database?
.. common events
.. purchase/token data
- add route to show value assigned to wallet?
- build route that tells someone how much they have locked
- set vestingBegin_ms to proper timestamp (current setting is for testing)
.. set the periods correctly (30 days apart?)

Complete
- restart with PROD; move CFG back to docker .env
.. verify wallet address
- disable /payment route (only for testing)
.. set debug flag?
- log to database?
.. common events
.. purchase/token data
- add route to show value assigned to wallet?
- /utils/ergoTreeToAddress/{ergoTreeHex} can convert from ergotree (in R4)
- push changes
.. remove keys
.. merge to main 
- set vestingBegin_ms to proper timestamp (current setting is for testing)
.. set the periods correctly (30 days apart?)
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

#region ROUTES
# current node info (and more)
@r.get("/info", name="blockchain:info")
async def getInfo():
  try:
    st = time() # stopwatch
    nodeInfo = {}    

    # ergonode
    res = requests.get(f'{CFG.node}/info', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), timeout=2)
    if res.ok:
      i = res.json()
      # nodeInfo['network'] = Network
      # nodeInfo['uri'] = CFG.node
      nodeInfo['ergonodeStatus'] = 'ok'
      if 'headersHeight' in i: nodeInfo['currentHeight'] = i['headersHeight']
      if 'currentTime' in i: nodeInfo['currentTime_ms'] = i['currentTime']
    else:
      nodeInfo['ergonode'] = 'error'

    # assembler
    res = requests.get(f'{CFG.assembler}/state', headers=headers, timeout=2)
    if res.ok:
      nodeInfo['assemblerIsFunctioning'] = res.json()['functioning']      
      nodeInfo['assemblerStatus'] = 'ok'
    else:
      nodeInfo['assemblerIsFunctioning'] = 'invalid'
      nodeInfo['assemblerStatus'] = 'error'

    # wallet and token
    # CAREFULL!!! XXX nodeInfo['apikey'] = CFG.ergopadApiKey XXX
    nodeInfo['network'] = Network
    nodeInfo['ergopadTokenId'] = CFG.ergopadTokenId
    if DEBUG: 
      nodeInfo['buyer'] = buyerWallet.address
    nodeInfo['seller'] = nodeWallet.address 

    # nodeInfo['vestingBegin_ms'] = f'{ctime(1643245200)} UTC'
    nodeInfo['sigUSD'] = await get_asset_current_price('sigusd')
    nodeInfo['inDebugMode'] = ('PROD', '!! DEBUG !!')[DEBUG]

    logging.debug(f'::TOOK {time()-st:0.4f}s')
    return nodeInfo

  except Exception as e:
    logging.error(f'ERR:{myself()}: invalid blockchain info ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid blockchain info')

# info about token
@r.get("/tokenInfo/{tokenId}", name="blockchain:tokenInfo")
def getTokenInfo(tokenId):
  # tkn = requests.get(f'{CFG.node}/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': CFG.apiKey})
  try:
    tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
    return tkn.json()
  except Exception as e:
    logging.error(f'ERR:{myself()}: invalid token request ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid token request')

# special request for CMC
@r.get("/emissionAmount/{tokenId}", name="blockchain:emissionAmount")
def getEmmissionAmount(tokenId):
  try:
    tkn = requests.get(f'{CFG.explorer}/tokens/{tokenId}')
    decimals = tkn.json()['decimals']
    emissionAmount = tkn.json()['emissionAmount'] / 10**decimals
    return emissionAmount
  except Exception as e:
    logging.error(f'ERR:{myself()}: invalid token request ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid token request')

# assember follow info
@r.get("/followInfo/{followId}", name="blockchain:followInfo")
def followInfo(followId):    
  try:
    res = requests.get(f'{CFG.assembler}/result/{followId}')
    return res.json()
    
  except Exception as e:
    logging.error(f'ERR:{myself()}: invalid assembly follow ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid assembly follow')

# find unspent boxes with tokens
@r.get("/unspentTokens", name="blockchain:unspentTokens")
def getBoxesWithUnspentTokens(nErgAmount=-1, tokenId=CFG.ergopadTokenId, tokenAmount=-1, allowMempool=True):
  try:
    foundTokenAmount = 0
    foundNErgAmount = 0
    ergopadTokenBoxes = {}    

    res = requests.get(f'{CFG.node}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}))
    if res.ok:
      assets = res.json()
      for ast in assets:
        if 'box' in ast:
          
          # find enough boxes to handle nergs requested
          if foundNErgAmount < nErgAmount or nErgAmount == -1:
            foundNErgAmount += ast['box']['value']
            ergopadTokenBoxes[ast['box']['boxId']] = []
          
          # find enough boxes with tokens to handle request
          if ast['box']['assets'] != [] and (foundTokenAmount < tokenAmount or tokenAmount == -1):
            for tkn in ast['box']['assets']:
              if 'tokenId' in tkn and 'amount' in tkn:
                 #logging.info(tokenId)
                if tkn['tokenId'] == tokenId:
                  foundTokenAmount += tkn['amount']
                  if ast['box']['boxId'] in ergopadTokenBoxes:
                    ergopadTokenBoxes[ast['box']['boxId']].append(tkn)
                  else:
                    ergopadTokenBoxes[ast['box']['boxId']] = [tkn]
                    foundNErgAmount += ast['box']['value']
                  # logging.debug(tkn)

      logging.info(f'found {foundTokenAmount} ergopad tokens and {foundNErgAmount} nErg in wallet')

    # invalid wallet, no unspent boxes, etc..
    else:
      logging.error('unable to find unspent boxes')

    # return CFG.node
    # return f'{CFG.node}/wallet/boxes/unspent?minInclusionHeight=0&minConfirmations={(0, -1)[allowMempool]}, apikey={CFG.ergopadApiKey}'
    return ergopadTokenBoxes

  except Exception as e:
    logging.error(f'ERR:{myself()}: unable to find unspent tokens ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to find unspent tokens')

# ergoscripts
@r.get("/script/{name}", name="blockchain:getErgoscript")
def getErgoscript(name, params={}):
  try:
    if name == 'alwaysTrue':
      script = f"""{{
        val x = 1
        val y = 1

        sigmaProp( x == y )
      }}"""

    if name == 'neverTrue':
      script = "{ 1 == 0 }"

    # params = {'buyerWallet': '3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG'}
    if name == 'ergopad':
      script = f"""{{
        val buyer = PK("{params['buyerWallet']}").propBytes
        val seller = PK("{params['nodeWallet']}").propBytes // ergopad.io
        val isValid = {{
            // 
            val voucher = OUTPUTS(0).R4[Long].getOrElse(0L)

            // voucher == voucher // && // TODO: match token
            buyer == INPUTS(0).propositionBytes
        }}

        sigmaProp(1==1)
      }}"""


    if name == 'directSale' or name == 'vesting1' or name == 'vesting2':
      with open(f'contracts/{name}.es') as f:
        unformattedScript = f.read()
      script = unformattedScript.format(**params)


    logging.debug(f'Script: {script}')
    # get the P2S address (basically a hash of the script??)
    p2s = requests.post(f'{CFG.assembler}/compile', headers=headers, json=script)
    logging.debug(f'p2s: {p2s.content}')
    smartContract = p2s.json()['address']
    # logging.debug(f'smart contract: {smartContract}')
    # logging.info(f':::{name}:::{script}')

    return smartContract
  
  except Exception as e:
    logging.error(f'ERR:{myself()}: unable to build script ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to build script')

@r.get("/allowance/{wallet}", name="blockchain:whitelist")
async def allowance(wallet:str):
  # round not used for now
  logging.info(f'Strategic sigusd remaining for: {wallet}...')
  await handleAllowance()

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

    with open(f'remaining.tsv') as f:
      for row in f.readlines():
        try:
          r = row.rstrip().split('\t')
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
    logging.error(f'{myself()}: {e}')

  if wallet in remaining:
    logging.debug(f'WALLET::{wallet}')
    if remaining[wallet]['remaining'] < 1:
      logging.error(f'ERR:{myself()}: blacklisted ({wallet})')
      # return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'blacklisted')

  if wallet in whitelist:
    r = whitelist[wallet]['amount']
    spent = 0
    if wallet in remaining:
      r = remaining[wallet]['remaining']
      spent = remaining[wallet]['spent']
    logging.info(f"sigusd: {whitelist[wallet]['amount']}")
    if spent == -1.0:
      return {'wallet': wallet, 'sigusd': -1.0, 'message': 'pending'}  
    else:
      return {'wallet': wallet, 'sigusd': r, 'message': 'remaining sigusd'}

  logging.info(f'sigusd: 0 (not found)')
  return {'wallet': wallet, 'sigusd': 0.0, 'message': 'not found'}
#endregion ROUTES

### MAIN
if __name__ == '__main__':
    print('API routes: ...')