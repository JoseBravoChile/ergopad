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
-
"""
#endregion BLOCKHEADER

#region INIT
DEBUG = CFG.debug
st = time() # stopwatch

DATABASE = CFG.connectionString

class TokenPurchase(BaseModel):
    wallet: str
    amount: float
    isToken: Optional[bool] = True
    currency: Optional[str] = 'sigusd'
    eventName: Optional[str] = 'presale-ergopad-202201'
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

# purchase tokens
@r.post("/", name="purchase:purchase")
async def purchaseToken(tokenPurchase: TokenPurchase):
    # early check
    try:
        nodeInfo = await getInfo()
        now = int(nodeInfo['currentTime_ms']/1000.0)
    except:
        now = int(time())
        pass
    logging.debug(now)

    con = create_engine(DATABASE)
    sql = f"""
        select description, total_sigusd, buffer_sigusd, walledId, start_dtz, end_dtz
            , tkn.address as tknAddress, tkn.decimals as tknDecimals
            , tkn.address as sigusdAddress, tkn.decimals as sigusdDecimals
        from events evt
            join tokens tkn on tkn.id = evt.vestingTokenId
            join tokens sigusd on sigusd.name = 'sigusd_v2'
        where "name" = '{tokenPurchase.eventName}'
            and "isWhitelist" = 0
    """
    logging.debug(sql)
    res = con.execute(sql).fetchone()
    if now < res['start_dtz'] or now > res['end_dtz']:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid time')

    # handle price exceptions
    tokenId = res['address']
    priceOverride = -1.0
    price = priceOverride
    try:
        sigusdCurrentPrice = await get_asset_current_price('sigusd') #Confusing naming, is this erg price in sigusd?
        if 'price' in sigusdCurrentPrice:
            price = sigusdCurrentPrice['price']
            if math.isnan(price): # NaN
                price = priceOverride
            if price < 1 or price > 1000: # OOS
                price = priceOverride
        if price == -1.0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid price found for sigusd')

    except Exception as e:
        logging.error(f'{myself()}: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid price found for sigusd')
        pass

    # handle token params
    ergopadDecimals = 10**res['tknDecimals']
    sigusdDecimals = 10**res['sigusdDecimals']

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
        strategic2Sigusd   = res['tokenPrice'] # strategic round .02 sigusd per token (50 strategic tokens per sigusd)
        tokenAmount        = int(amount/strategic2Sigusd)*ergopadDecimals
        coinAmount_nerg    = int(amount/price*nergsPerErg)
        sendAmount_nerg    = coinAmount_nerg+2*txFee_nerg
        if isToken:
            coinAmount_nerg  = txFee_nerg # min per box
            sendAmount_nerg  = 10000000 # coinAmount_nerg+txMin_nerg # +txFee_nerg

        logging.info(f'using {tokenName}, amount={tokenAmount/ergopadDecimals:.2f} at price={price} for {amount}sigusd')

        # check whitelist
        walletId = -1
        eventId = -1
        try:
            sql = f"""
                with wal as (
                    select id
                    from wallets
                    where address = '{tokenPurchase.wallet}'
                )
                select
                    wal.id as "walletId"
                    evt.id as "eventId"
                    , wht.allowance_sigusd
                    , sum(coalesce(pur.currencyAmount, 0.0)) as spent_sigusd
                    , sum(coalesce(pur.currencyAmount, 0.0)) as remaining_sigusd
                from purchases pur
                    join wal on wal.id = pur."walletId"                
                    join events evt on evt.id = put.eventId
                    join whitelist wht on wht."eventId" = evt.id
                        and wht."walletId" = wal.id
                where
                    evt.name = '{tokenPurchase.eventName}'
                group by 
                    wal.id
                    , evt.id
                    , wht.allowance_sigusd
            """
            res = con.execute(sql).fetchone()
            walletId = res['walletId']
            eventId = res['eventId']

        except Exception as e:
            logging.error(f'ERR:{myself()}: reading whitelist ({e})')
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid purchase')

        # make sure buyer is whitelisted
        if res.rowcount == 0:
            logging.debug(f'invalid whitelist for wallet')
            return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'wallet, {buyerWallet.address} invalid whitelist for wallet')

        # make sure buyer remains under amount limit
        if amount > res['remaining_sigusd']:
            logging.debug(f"amount ({amount}) exceeds whitelist amount: {res['spent_sigusd']} spent, {res['remaining_sigusd']} remaining")
            return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content=f'amount {amount}sigusd exceeds remaining allowance')

        # 1 outbox per vesting period to lock spending until vesting complete
        logging.info(f'wallet: ok\nwhitelist: ok\nergs: {coinAmount_nerg} at price {price}')
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

        # save purchase info
        try:
            sql = f"""
                insert purchases (walletId, eventId, toAddress, currency, currencyAmount, feeAmount)
                values ('{walletId}', {eventId}, '{scPurchase}', '{tokenPurchase.currency}', {amount}, {txFee_nerg})
            """
            res = con.execute(sql)
        except:
            logging.error(f'ERR:{myself()}: unable to save purchase ({e})')
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to save purchase')
            pass

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

        # make async request to assembler
        res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)
        logging.debug(res)
        id = res.json()['id']
        fin = requests.get(f'{CFG.assembler}/result/{id}')
        logging.info({'status': 'success', 'fin': fin.json(), 'followId': id})

        logging.debug(f'::TOOK {time()-st:.2f}s')
        if isToken:
            message = f'send {sendAmount_nerg/nergsPerErg} ergs and {amount} sigusd to {scPurchase}'
        else:
            message = f'send {sendAmount_nerg/nergsPerErg} ergs to {scPurchase}'
        return({
                'status'        : 'success',
                'message'       : message,
                'total'         : sendAmount_nerg/nergsPerErg,
                'assembler'     : json.dumps(fin.json()),
                'smartContract' : scPurchase,
                'request'       : json.dumps(request),
        })

    except Exception as e:
        logging.error(f'ERR:{myself()}: building request ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'building request')

@r.get("/allowance/{wallet}", name="purchase:allowance")
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

# TEST - send payment from test wallet
@r.get("/sendPayment/{address}/{nergs}/{tokens}", name="purchase:sendPayment")
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
