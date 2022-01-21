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
        headers = {'Content-Type': 'application/json', 'api_key': CFG.ergopadApiKey}
        res = requests.get('http://ergonode:9053/wallet/transactions', headers=headers)
        totTokens = 0
        if res.ok:
            tx = res.json()
            for t in tx:
                # print(f"tx: {t['id']}")
                for o in t['outputs']:
                    if 'assets' in o and 'additionalRegisters' in o:
                        if o['address'] != '9gibNzudNny7MtB725qGM3Pqftho1SMpQJ2GYLYRDDAftMaC285' and 'R5' in o['additionalRegisters']:
                            if o['additionalRegisters']['R5'] == '0580e4a0ca13':
                                for a in o['assets']:
                                    if 'tokenId' in a:
                                        if a['tokenId'] == 'd71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413':
                                            totTokens += a['amount']/100

        con = create_engine(DATABASE)
        sql = f"""
            with evt as (
                select id
                from events
                where name = 'presale-ergopad-202201wl'
            )
            , pur as (
                select 3 as id
                    , sum(coalesce("tokenAmount"/100, 0.0)) as spent_ergopad
                from purchases 
                where "assemblerStatus" = 'success' 
                    and id > 0
                    and currency = 'ergo'
                    and "eventName" = 'presale-ergopad-202201wl'
            )
            , exg_strat as (
                select 3 as id
                    , sum(coalesce("tokenAmount"/100, 0.0)) as spent_ergopad
                from purchases 
                where "assemblerStatus" = 'success' 
                    and id > 0
                    and currency = 'strategic_sale'
                    and "eventName" = 'presale-ergopad-202201wl'
            )
            , exg_seed as (
                select 3 as id
                    , sum(coalesce("tokenAmount"/100, 0.0)) as spent_ergopad
                from purchases 
                where "assemblerStatus" = 'success' 
                    and id > 0
                    and currency = 'seedsale'
                    and "eventName" = 'presale-ergopad-202201wl'
            )
            select evt.id
                , coalesce(sum(allowance_sigusd), 0.0) as allowance_sigusd
				, coalesce(sum(spent_sigusd), 0.0) as spent_sigusd
                , coalesce(count(*), 0.0) as entries
                , coalesce(max(created_dtz), '1/1/1900') as last_entry
				, coalesce(max(pur.spent_ergopad), 0.0) as spent_ergopad_presale
				, coalesce(max(exg_strat.spent_ergopad), 0.0) as spent_ergopad_strategic
				, coalesce(max(exg_seed.spent_ergopad), 0.0) as spent_ergopad_seedsale
            from whitelist wht
                join evt on evt.id = wht."eventId"
                join pur on pur.id = wht."eventId"
                join exg_strat on exg_strat.id = wht."eventId"
                join exg_seed on exg_seed.id = wht."eventId"
            where "isWhitelist" = 1
            group by evt.id;
        """
        res = con.execute(sql).fetchone()

        return {
            'event': eventName,
            'id': res['id'],
            'total (sigusd)': f"\u01A9\u0024{res['allowance_sigusd']:,.2f}",
            'spent (sigusd)': f"\u01A9\u0024{res['spent_sigusd']:,.2f}",
            'remaining (sigusd)': f"\u01A9\u0024{res['allowance_sigusd']-res['spent_sigusd']:,.2f}",
            'spent presale (ergopad)': f"\u2234{totTokens:,.2f} tokens",
            'spent strategic (ergopad)': f"\u2234{res['spent_ergopad_strategic']:,.2f} tokens",
            'spent seedsale (ergopad)': f"\u2234{res['spent_ergopad_seedsale']:,.2f} tokens",
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
