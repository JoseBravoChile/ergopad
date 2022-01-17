import requests, json, os

from starlette.responses import JSONResponse 
from sqlalchemy import create_engine
from fastapi import APIRouter, Response, status #, Request
from time import time
from datetime import datetime as dt
from config import Config, Network # api specific config
CFG = Config[Network]

events_router = r = APIRouter()

#region BLOCKHEADER
"""
Events API
---------
Created: vikingphoenixconsulting@gmail.com
On: 20220113
Purpose: allow wallets to be whitelisted
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

DEBUG = True
st = time() # stopwatch
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

@r.get("/summary/{eventName}")
def summary(eventName):
    try:
        con = create_engine(DATABASE)
        sql = f"""
            with evt as (
                select id
                from events
                where name = 'presale-ergopad-202201wl'
            )
            select evt.id
                , coalesce(sum(allowance_sigusd), 0.0) as sigusd
                , coalesce(count(*), 0.0) as entries
                , coalesce(max(created_dtz), '1/1/1900') as last_entry
            from whitelist wht
                join evt on evt.id = wht."eventId"
            group by evt.id;
        """
        res = con.execute(sql).fetchone()
        return {
            'event': eventName,
            'id': res['id'],
            'total (sigusd)': f"\u01A9\u0024{res['sigusd']:,.2f}",
            # 'total (ergo) apx.': f"~\u2234{res['sigusd']*sig2erg:,.2f}",
            'number of entries': res['entries'],
            'time of last entry': res['last_entry'],
        }

    except Exception as e:
        logging.error(f'ERR:{myself()}: events info {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid events request')

@r.get("/info/{eventName}")
def events(eventName):
    # return {'hello': 'world'}
    try:
        if eventName != '_':
            where = f"where name = '{eventName}'"
        else:
            where = ''
        con = create_engine(DATABASE)
        sql = f"""
            select id, name, description, total_sigusd, buffer_sigusd, "walletId", "individualCap", "vestedTokenId", "vestingPeriods", "vestingPeriodDuration", "vestingPeriodType", "tokenPrice", "isWhitelist", start_dtz, end_dtz
            from events
            {where}
        """
        # logging.debug(sql)
        res = con.execute(sql)
        # logging.debug(res)
        events = []
        for r in res:
            events.append({
                "id": r['id'],
                "name": r['name'],
                "description": r['description'],
                "total_sigusd": r['total_sigusd'],
                "buffer_sigusd": r['buffer_sigusd'],
                "walletId": r['walletId'],
                "individualCap": r['individualCap'],
                "vestedTokenId": r['vestedTokenId'],
                "vestingPeriods": r['vestingPeriods'],
                "vestingPeriodDuration": r['vestingPeriodDuration'],
                "vestingPeriodType": r['vestingPeriodType'],
                "tokenPrice": r['tokenPrice'],
                "isWhitelist": r['isWhitelist'],
                "start_dtz": r['start_dtz'],
                "end_dtz": r['end_dtz'],
            })
        return events

    except:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'invalid events request')
