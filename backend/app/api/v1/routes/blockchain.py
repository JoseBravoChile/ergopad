import requests, json, os
import math
from starlette.responses import JSONResponse 
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time, ctime
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode
from ergo.updateAllowance import handleAllowance
from ergo.util import encodeLong, encodeString
import uuid

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

DEBUG = True
st = time() # stopwatch

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region INIT
class TokenPurchase(BaseModel):
  wallet: str
  amount: float
  isToken: Optional[bool] = True
  currency: Optional[str] = 'sigusd'

try:
  CFG = Config[Network]
  headers            = {'Content-Type': 'application/json'}
  tokenInfo          = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')

  if Network == 'testnet':
    validCurrencies    = {
      'seedsale' : '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
      'sigusd'   : '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
      'ergopad'  : '5ff2d1cc22ebf959b1cc65453e4ee225b0fdaf4c38a12e3b4ba32ff769bed70f', # 
      # 'sigusd'   : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD
      # 'ergopad'  : '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d', # TODO: need official ergonad token
      # 'kushti' : '??',
      # '$COMET' : '??',
    }

    #CFG.node           = 'http://ergonode:9052'
    #CFG.assembler      = 'http://assembler:8080'
    #CFG.ergopadApiKey  = 'oncejournalstrangeweather'

    nodeWallet         = Wallet('3WxMzA9TwMYh9M5ivSfHi5VqUDhUS6nX4B8ZQNqGLupZqZfivmUw') # contains tokens
    buyerWallet        = Wallet('3WzKuUxmG7HtfmZNxxHw3ArPzsZZR96yrNkTLq4i1qFwVqBXAU8M') # simulate buyer

  # mainnet
  else:
    validCurrencies    = {
      # 'seedsale' : '8eb9a97f4c8e5409ade9a13625f2bbb9f8b081e51d37f623233444743fae8321', # xeed1k
      # 'sigusd'   : '8eb9a97f4c8e5409ade9a13625f2bbb9f8b081e51d37f623233444743fae8321', # xeed1k
      # 'sigusd'   : '29275cf36ffae29ed186df55ac6f8d47b367fe8e398721e200acb71bc32b10a0', # xyzpad
      # 'sigusd'   : '191dd93523e052d9be49680508f675f82e461ef5452d60143212beb42b7f62a8',
      # 'ergopad'  : 'cc3c5dc01bb4b2a05475b2d9a5b4202ed235f7182b46677ed8f40358333b92bb', # xerg10M / TESTING, strategic token
      'ergopad'  : '60def1ed45ffc6493c8c6a576c7a23818b6b2dfc4ff4967e9867e3795886c437', # official
      'sigusd'   : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD (SigmaUSD - V2)
      # 'ergopad'  : 'cc3c5dc01bb4b2a05475b2d9a5b4202ed235f7182b46677ed8f40358333b92bb', # TODO: need official ergopad token
      # 'kushti' : '??',
      # '$COMET' : '??',
    }

    # CFG.node           = 'http://73.203.30.137:9053'
    # CFG.assembler      = 'http://73.203.30.137:8080'
    CFG.node           = 'http://38.15.40.14:9053'
    CFG.assembler      = 'http://38.15.40.14:8888'
    CFG.ergopadApiKey  = 'headerbasketcandyjourney'
    nodeWallet         = Wallet('9gibNzudNny7MtB725qGM3Pqftho1SMpQJ2GYLYRDDAftMaC285') # contains ergopad tokens (xerg10M)
    # buyerWallet        = Wallet('9f2sfNnZDzwFGjFRqLGtPQYu94cVh3TcE2HmHksvZeg1PY5tGrZ') # simulate buyer / seed tokens
    buyerWallet        = Wallet('9iLSsvi2zobapQmi7tXVK4mnrbQwpK3oTfPcCpF9n7J2DQVpxq2') # simulate buyer / seed tokens

  CFG.ergopadTokenId = validCurrencies['ergopad'] 
  CFG.seedTokenId    = validCurrencies['seedsale']
  CFG.sigusdTokenId  = validCurrencies['sigusd']

except Exception as e:
  logging.error(f'Init {e}')
#endregion INIT

blockchain_router = r = APIRouter()

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

# TEST - send payment from test wallet
@r.get("/sendPayment/{address}/{nergs}/{tokens}", name="blockchain:sendPayment")
def sendPayment(address, nergs, tokens):
  # TODO: require login/password or something; disable in PROD
  try:
    if not DEBUG:
      return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=f'not found')
      # return {'status': 'fail', 'detail': f'only available in DEBUG mode'}    

    sendMe = ''
    isWalletLocked = False
    
    # !! add in check for wallet lock, and unlock/relock if needed
    lck = requests.get(f'http://ergonode2:9052/wallet/status', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'})
    logging.info(lck.content)
    if lck.ok:
        if lck.json()['isUnlocked'] == False:
            ulk = requests.post(f'http://ergonode2:9052/wallet/unlock', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'}, json={'pass': 'crowdvacationancientamber'})
            logging.info(ulk.content)
            if ulk.ok: isWalletLocked = False
            else: isWalletLocked = True
        else: isWalletLocked = True
    else: isWalletLocked = True

    # unlock wallet
    if isWalletLocked:
        logging.info('unlock wallet')

    # send nergs to address/smartContract from the buyer wallet
    # for testing, address/smartContract is 1==1, which anyone could fulfill
    sendMe = [{
        'address': address,
        'value': int(nergs),
        'assets': [{"tokenId": validCurrencies['seedsale'], "amount": tokens}],
        # 'assets': [],

    }]
    pay = requests.post(f'http://ergonode2:9052/wallet/payment/send', headers={'Content-Type': 'application/json', 'api_key': 'goalspentchillyamber'}, json=sendMe)

    # relock wallet
    if not isWalletLocked:
        logging.info('relock wallet')

    return {'status': 'success', 'detail': f'payment: {pay.json()}'}

  except Exception as e:
    logging.error(f'ERR:{myself()}: unable to send payment ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to send payment')

### MAIN
if __name__ == '__main__':
    print('API routes: ...')