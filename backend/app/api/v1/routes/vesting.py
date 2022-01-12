import requests, json, os
import math
from starlette.responses import JSONResponse 
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time
from datetime import date
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode
from ergo.updateAllowance import handleAllowance
from ergo.util import encodeLong, encodeString
import uuid
from hashlib import blake2b
from api.v1.routes.blockchain import getTokenInfo, getErgoscript, getBoxesWithUnspentTokens

DEBUG = True
st = time() # stopwatch

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

vesting_router = r = APIRouter()

CFG = Config[Network]

nergsPerErg        = 1000000000
headers            = {'Content-Type': 'application/json'}

duration_ms = {
    'month': 30*24*60*60*1000,
    'week': 7*24*60*60*1000,
    'day': 24*60*60*1000,
    'minute': 60*1000
}

class Vestment(BaseModel):
    wallet: str
    vestingAmount: float
    currency: Optional[str] = 'sigusd'
    currencyPrice: Optional[float] = None
    vestedToken: Optional[str] = 'ergopad'
    vestedTokenPrice: Optional[float] = None
    vestingPeriods: float
    periodDuration: float
    periodType: str
    vestingBegin: Optional[float] = int(time()*1000)


# purchase tokens
@r.post("/vest/", name="vesting:vestToken")
async def vestToken(vestment: Vestment): 

    if vestment.currencyPrice is None:
        vestment.currencyPrice = (await get_asset_current_price(vestment.currency))["price"]
    if vestment.vestedTokenPrice is None:
        vestment.vestedTokenPrice = (await get_asset_current_price(vestment.vestedToken))["price"]
    isToken = vestment.currency != "ergo"
    logging.info(f'Price info: {vestment.currency} = {vestment.currencyPrice} USD, {vestment.vestedToken} = {vestment.vestedTokenPrice}')

    # handle token params
    currencyDecimals = 0
    vestedTokenDecimals = 0
    try:
        if isToken:
            tokenDecimals = getTokenInfo(CFG.validCurrencies[vestment.currency])
            logging.debug(tokenDecimals)
            if 'decimals' in tokenDecimals:
                currencyDecimals = int(tokenDecimals['decimals'])
        else:
            currencyDecimals = 9
        tokenDecimals = getTokenInfo(CFG.validCurrencies[vestment.vestedToken])
        if 'decimals' in tokenDecimals:
            vestedTokenDecimals = int(tokenDecimals['decimals'])
    except Exception as e:
        logging.error(f'{myself()}: {e}')
        logging.error('invalid decimals found for sigusd')
        pass

    logging.info(f'decimals for currency: {currencyDecimals}, vestedToken: {vestedTokenDecimals}')
    vestedTokenDecimals = 10**vestedTokenDecimals
    currencyDecimals = 10**currencyDecimals

    try:
        buyerWallet        = Wallet(vestment.wallet)
        nodeWallet = Wallet(CFG.nodeWallet)
        amountInUSD             = vestment.vestingAmount*vestment.vestedTokenPrice
        
        vestingDuration_ms = duration_ms[vestment.periodType]*vestment.periodDuration
        vestingBegin_ms    = vestment.vestingBegin

        txFee_nerg         = int(.001*nergsPerErg)

        tokenAmount        = vestment.vestingAmount*vestedTokenDecimals
        logging.info(f"1 {amountInUSD}")
        currencyAmount = amountInUSD/vestment.currencyPrice
        coinAmount_nerg    = int(.01*nergsPerErg)
        if vestment.currency == "ergo":
            coinAmount_nerg = int(currencyAmount*nergsPerErg)
        sendAmount_nerg    = coinAmount_nerg

        logging.info(f'using {vestment.currency}, amount={vestment.vestingAmount:.2f} at price={vestment.vestedTokenPrice} for {amountInUSD}sigusd')

        # pay ergopad for tokens with coins or tokens
        startWhen = {'erg': sendAmount_nerg}
        outBox = [{
            'address': nodeWallet.address, 
            'value': sendAmount_nerg 
        }]
        if isToken:
            outBox[0]['assets'] = [{
                'tokenId': CFG.validCurrencies[vestment.currency], # sigusd
                'amount': int(currencyAmount*currencyDecimals),
            }]
            startWhen[CFG.validCurrencies[vestment.currency]] = int(currencyAmount*currencyDecimals)
    
        logging.info(f'startWhen: {startWhen}')

        scVesting = getErgoscript('vesting2', params={})

        # create outputs for each vesting period; add remainder to final output, if exists
        r4 = encodeString(buyerWallet.ergoTree()) # convert to bytearray
        r5 = encodeLong(int(vestingDuration_ms))
        r6 = encodeLong(int(tokenAmount/vestment.vestingPeriods))
        r7 = encodeLong(int(vestingBegin_ms))
        r8 = encodeLong(int(tokenAmount))
        r9 = encodeString(uuid.uuid4().hex)
        outBox.append({
            'address': scVesting,
            'value': txFee_nerg,
            'registers': {
                'R4': r4,
                'R5': r5,
                'R6': r6,
                'R7': r7,
                'R8': r8,
                'R9': r9
            },
            'assets': [{ 
                'tokenId': CFG.validCurrencies[vestment.vestedToken],
                'amount': tokenAmount
            }]
        })
        currencyID = CFG.validCurrencies[vestment.currency] if isToken else ""
        params = {
            'nodeWallet': nodeWallet.address,
            'buyerWallet': buyerWallet.address,
            'vestingErgoTree': b64encode(bytes.fromhex(Wallet(scVesting).ergoTree()[2:])).decode('utf-8'),
            'saleToken': b64encode(bytes.fromhex(CFG.validCurrencies[vestment.vestedToken])).decode('utf-8'),
            'saleTokenAmount': int(tokenAmount),
            'timestamp': int(time()),
            'purchaseToken': b64encode(bytes.fromhex(currencyID)).decode('utf-8'),
            'purchaseTokenAmount': int(currencyAmount*currencyDecimals),
            'redeemPeriod': int(vestingDuration_ms),
            'redeemAmount': int(tokenAmount/vestment.vestingPeriods),
            'vestingStart': int(vestingBegin_ms)
        }
        logging.info(params)
        scPurchase = getErgoscript('vesting1', params=params)
        # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
        ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId=CFG.validCurrencies[vestment.vestedToken], nErgAmount=txFee_nerg*3, tokenAmount=tokenAmount)
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

        logging.debug(f'::TOOK {time()-st:.2f}s')
        if isToken:
            message = f'send {sendAmount_nerg/nergsPerErg} ergs and {currencyAmount} {vestment.currency} to {scPurchase}'
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

# redeem/disburse tokens after lock
@r.get("/redeem/{address}", name="vesting:redeem")
def redeemToken(address:str):

    txFee_nerg = CFG.txFee
    txBoxTotal_nerg = 0
    scPurchase = getErgoscript('alwaysTrue', {})
    outBoxes = []
    inBoxes = []
    currentTime = requests.get(f'{CFG.node}/blocks/lastHeaders/1', headers=dict(headers),timeout=2).json()[0]['timestamp']
    offset = 0
    res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={offset}&limit=500', headers=dict(headers), timeout=2) #This needs to be put in a loop in case of more than 500 boxes
    while res.ok:
        rJson = res.json()
        logging.info(rJson['total'])
        for box in rJson['items']:
            if len(outBoxes) > 500:
                break
            nodeRes = requests.get(f"{CFG.node}/utils/ergoTreeToAddress/{box['additionalRegisters']['R4']['renderedValue']}").json()
            buyerAddress = nodeRes['address']
            redeemPeriod = int(box['additionalRegisters']['R5']['renderedValue'])
            redeemAmount = int(box['additionalRegisters']['R6']['renderedValue'])
            vestingStart = int(box['additionalRegisters']['R7']['renderedValue'])
            totalVested = int(box['additionalRegisters']['R8']['renderedValue'])
            timeVested = int(currentTime - vestingStart)
            periods = int(timeVested/redeemPeriod)
            redeemed = totalVested - box['assets'][0]['amount']
            totalRedeemable = periods * redeemAmount
            redeemableTokens = totalVested - redeemed if (totalVested-totalRedeemable) < redeemAmount else totalRedeemable - redeemed
            if redeemableTokens > 0:
                if (totalVested-(redeemableTokens+redeemed))>0:
                    outBox = {
                        'address': box['address'],
                        'value': box['value'],
                        'registers': {
                        'R4': box['additionalRegisters']['R4']['serializedValue'],
                        'R5': box['additionalRegisters']['R5']['serializedValue'],
                        'R6': box['additionalRegisters']['R6']['serializedValue'],
                        'R7': box['additionalRegisters']['R7']['serializedValue'],
                        'R8': box['additionalRegisters']['R8']['serializedValue'],
                        'R9': box['additionalRegisters']['R9']['serializedValue']
                        },
                        'assets': [{
                        'tokenId': box['assets'][0]['tokenId'],
                        'amount': (totalVested-(redeemableTokens+redeemed))
                        }]
                    }
                    txBoxTotal_nerg += box['value']
                    outBoxes.append(outBox)
                outBox = {
                'address': str(buyerAddress),
                'value': txFee_nerg,
                'assets': [{
                    'tokenId': box['assets'][0]['tokenId'],
                    'amount': redeemableTokens
                }],
                'registers': {
                    'R4': box['additionalRegisters']['R9']['serializedValue']
                }
                }
                outBoxes.append(outBox)
                txBoxTotal_nerg += txFee_nerg
                inBoxes.append(box['boxId'])

        if len(res.json()['items']) == 500 and len(outBoxes) < 500:
            offset += 500
            res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={0}&limit=500', headers=dict(headers), timeout=2)
        else:
            break

    # redeem
    if len(outBoxes) > 0:
        
        ergopadTokenBoxes = getBoxesWithUnspentTokens(tokenId="", nErgAmount=txBoxTotal_nerg, tokenAmount=0)
        request = {
            'address': scPurchase,
            'returnTo': CFG.nodeWallet,
            'startWhen': {
                'erg': 0, 
            },
            'txSpec': {
                'requests': outBoxes,
                'fee': txFee_nerg,          
                'inputs': inBoxes+list(ergopadTokenBoxes.keys()),
                'dataInputs': [],
            },
        }

        # make async request to assembler
        # logging.info(request); exit(); # !! testing
        logging.debug(request)
        res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)   
        logging.debug(res)

    try:
        return({
            'status': 'success', 
            #'details': f'send {txFee_nerg} to {scPurchase}',
        })
    
    except Exception as e:
        logging.error(f'ERR:{myself()}: unable to redeem ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to redeem')

# find vesting/vested tokens
@r.get("/vested/{wallet}", name="vesting:findVestedTokens")
def findVestingTokens(wallet:str):
  try:
    #tokenId     = CFG.ergopadTokenId
    total       = 0
    result = {}
    userWallet = Wallet(wallet)
    userErgoTree = userWallet.ergoTree()
    address = getErgoscript('vesting2', params={}) # just a quick hack, is always the same so should just be part of the CFG
    offset = 0
    res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={offset}&limit=500', headers=dict(headers), timeout=2)
    while res.ok: 
        # returns array of dicts
        for box in res.json()["items"]:
            if box["additionalRegisters"]["R4"]["renderedValue"] == userErgoTree:
                tokenId = box["assets"][0]["tokenId"]
                if tokenId not in result:
                    result[tokenId] = {}
                    result[tokenId]['name'] = box["assets"][0]["name"]
                    result[tokenId]['totalVested'] = 0.0
                    result[tokenId]['outstanding'] = {}
                tokenDecimals = 10**box["assets"][0]["decimals"]
                initialVestedAmount = int(box["additionalRegisters"]["R8"]["renderedValue"])/tokenDecimals
                nextRedeemAmount = int(box["additionalRegisters"]["R6"]["renderedValue"])/tokenDecimals
                remainingVested = int(box["assets"][0]["amount"])/tokenDecimals
                result[tokenId]['totalVested'] += remainingVested
                nextRedeemTimestamp = (((initialVestedAmount-remainingVested)/nextRedeemAmount+1)*int(box["additionalRegisters"]["R5"]["renderedValue"])+int(box["additionalRegisters"]["R7"]["renderedValue"]))/1000.0
                nextRedeemDate = date.fromtimestamp(nextRedeemTimestamp)
                while remainingVested > 0:
                    if nextRedeemDate not in result[tokenId]['outstanding']:
                        result[tokenId]['outstanding'][nextRedeemDate] = {}
                        result[tokenId]['outstanding'][nextRedeemDate]['amount'] = 0.0
                    redeemAmount = nextRedeemAmount if remainingVested >= 2*nextRedeemAmount else remainingVested
                    result[tokenId]['outstanding'][nextRedeemDate]['amount'] += redeemAmount
                    remainingVested -= redeemAmount
                    nextRedeemTimestamp += int(box["additionalRegisters"]["R5"]["renderedValue"])/1000.0
                    nextRedeemDate = date.fromtimestamp(nextRedeemTimestamp)
        if len(res.json()['items']) == 500:
            offset += 500
            res = requests.get(f'{CFG.explorer}/boxes/unspent/byAddress/{address}?offset={0}&limit=500', headers=dict(headers), timeout=2)
        else:
            break
    
    resJson = []
    for key in result.keys():
        tokenResult = {}
        value = result[key]
        tokenResult['tokenId'] = key
        tokenResult['name'] = value['name']
        tokenResult['totalVested'] = value['totalVested']
        tokenResult['outstanding'] = []
        for redeemDate in sorted(value['outstanding'].keys()):
            tokenResult['outstanding'].append({'date': redeemDate, 'amount': value['outstanding'][redeemDate]['amount']})
        resJson.append(tokenResult)

    return({
        'status': 'success', 
        'vested': resJson
    })

  except Exception as e:
    logging.error(f'ERR:{myself()}: unable to build vesting request ({e})')
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to build vesting request')