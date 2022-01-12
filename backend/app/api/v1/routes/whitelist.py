from starlette.responses import JSONResponse 
from sqlalchemy import create_engine
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, Response, status #, Request
from fastapi.encoders import jsonable_encoder
from typing import Optional
from pydantic import BaseModel
from time import time
from datetime import datetime as dt

import requests, json, os
import pandas as pd

### ROUTER
whitelist_router = r = APIRouter()

#region BLOCKHEADER
"""
Whitelist API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20220111
Purpose: allow wallets to be whitelisted
Contributor(s): https://github.com/Luivatra

Notes: 
"""
#endregion BLOCKHEADER


#region INIT
CFG = Config[Network]

EVENTNAME = 'IDO'
EVENTID = 3 # lookup in public.events
MAXSIGUSD = 20000
DATEFORMAT = '%m/%d/%Y %H:%M'
EVENTBEGINS = int(dt.timestamp(dt.strptime('1/11/2022 00:00', DATEFORMAT)))
EVENTFINISH = int(dt.timestamp(dt.strptime('1/11/2022 23:59', DATEFORMAT)))
NOW = int(time())
ONAIR = (NOW > EVENTBEGINS) and (NOW < EVENTFINISH)

DATABASE = CFG.connectionString

DEBUG = True
st = time() # stopwatch
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)
# import coloredlogs
# coloredlogs.install(level=levelname, logger=logging.getLogger(__name__))

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region CLASSES
# dat = {'name': 'bob', 'email': 'email', 'qty': 9, 'wallet': '1234', 'handle1': 'h1', 'platform1': 'p1', 'handle2': 'h2', 'platform2': 'p2', 'canInvest': 1, 'hasRisk': 1, 'isIDO': 1}
class Whitelist(BaseModel):
    ergoAddress: str # wallet
    email: str
    event: str = EVENTNAME
    name: str
    sigValue: float
    socialHandle: str
    socialPlatform: str
    chatHandle: str
    chatPlatform: str

    class Config:
        schema_extra = {
            "example": {
                'ergoAddress': '3WzKuUxmG7HtfmZNxxHw3ArPzsZZR96yrNkTLq4i1qFwVqBXAU8X',
                'email': 'hello@world.com',
                'event': EVENTNAME,
                'name': 'Jo Smith',
                'sigValue': 2000.5,
                'socialHandle': '@tweetyBird',
                'socialPlatform': 'twitter',
                'chatHandle': '@puddyTat',
                'chatPlatform': 'discord',
            }
        }
#endregion CLASSES

#region ROUTES
@r.post("/whitelist")
async def email(whitelist: Whitelist, response: Response):
    try:
        if not ONAIR:
            response.status_code = status.HTTP_406_NOT_ACCEPTABLE
            return {'status': 'error', 'message': f'whitelist signup between {dt.fromtimestamp(EVENTBEGINS).strftime(DATEFORMAT)} and {dt.fromtimestamp(EVENTFINISH).strftime(DATEFORMAT)}'}

        logging.debug('ONAIR...')
        whitelist.sigValue = int(whitelist.sigValue)
        if whitelist.sigValue > MAXSIGUSD:
            whitelist.sigValue = MAXSIGUSD
        
        # find wallet
        logging.debug(f'connecting to: {CFG.connectionString}')
        con = create_engine(DATABASE)
        logging.debug('connected to database...')
        pd.options.mode.chained_assignment = None  # default='warn'
        df = pd.DataFrame(jsonable_encoder(whitelist), index=[0])
        logging.debug(f'dataframe: {df}')
        sqlFindWallet = f"select id from wallets where address = '{whitelist.ergoAddress}'"
        logging.debug(sqlFindWallet)
        res = con.execute(sqlFindWallet)
        # create wallet if it doesn't exist
        if res.rowcount == 0:
            dfWallet = df[['ergoAddress', 'email', 'socialHandle', 'socialPlatform', 'chatHandle', 'chatPlatform']]
            dfWallet['network'] = Network
            dfWallet['lastSeen_dtz'] = dt.fromtimestamp(NOW).strftime(DATEFORMAT)
            dfWallet['created_dtz'] = dt.fromtimestamp(NOW).strftime(DATEFORMAT)
            dfWallet = dfWallet.rename(columns={'ergoAddress': 'address'})
            logging.debug(f'save wallet: {dfWallet}')
            dfWallet.to_sql('wallets', con=con, if_exists='append', index=False)

        # check this wallet has not already registered for this event
        res = con.execute(sqlFindWallet).fetchone()
        walletId = res['id']
        sqlAlreadyWhitelisted = f'select id from "whitelist" where "walletId" = {walletId} and "eventId" = {EVENTID}'
        res = con.execute(sqlAlreadyWhitelisted)
        if res.rowcount == 0:
            # add whitelist entry
            logging.debug(f'found id: {walletId}')
            dfWhitelist = df[['sigValue']]
            dfWhitelist['walletId'] = walletId
            dfWhitelist['eventId'] = EVENTID
            dfWhitelist['created_dtz'] = dt.fromtimestamp(NOW).strftime(DATEFORMAT)
            dfWhitelist = dfWhitelist.rename(columns={'sigValue': 'allowance_sigusd'})
            dfWhitelist.to_sql('whitelist', con=con, if_exists='append', index=False)
            return {'status': 'success', 'detail': f'added to whitelist'}

        # already whitelisted
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'wallet already signed up for this event')

    except Exception as e:
        logging.error(f'ERR:{myself()}: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to save whitelist request')

@r.get("/whitelist")
async def whitelist():
    try:
        con = create_engine(DATABASE)
        res = con.execute(f"""
            select coalesce(sum("allowance_sigusd"), 0.0) as total
                , coalesce(sum("allowance_sigusd"), 0.0) - coalesce(sum("spent_sigusd"), 0.0) as remaining
            from "whitelist"
            where "eventId" = {EVENTID}
        """).fetchone()
        return {'status': 'success', 'total_sigusd': int(res['total']), 'remaining_sigusd': int(res['remaining']), 'gmt': NOW}

    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'unable to determine remaining whitelist sigUSD for event')
#endregion ROUTES

### MAIN
if __name__ == '__main__':
    print('API routes: ...')
