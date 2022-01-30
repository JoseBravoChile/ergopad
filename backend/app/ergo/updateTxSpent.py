import requests, json, os
from sqlalchemy import create_engine
from starlette.responses import JSONResponse 
from time import time, sleep
from datetime import date, datetime, timezone

import logging
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=logging.DEBUG)

import inspect
myself = lambda: inspect.stack()[1][3]

POWERNAP = 60 # s to sleep for infinite loop
DATABASE = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}"
ASSEMBLER = 'http://assembler:8080'
BACKEND = 'http://backend:8000'

totalVested = 0
i = 0
con = create_engine(DATABASE)
while True:
    try:
        # update spent for success
        sql = f"""
            select "assemblerId", "assemblerStatus", "walletAddress"
            from purchases
            where id > 0
                and "assemblerStatus" in ('success')
        """
        logging.debug(sql)
        res = con.execute(sql).fetchall()
        # logging.debug(res)

        for r in res:
            wallet = r['walletAddress']
            logging.debug(f'checking {wallet}')
            try:
                res = requests.get(f"{BACKEND}/api/vesting/vested/{wallet}")
                if res.ok:
                    logging.debug(res.json())
                    if 'vested' in res.json():
                        for v in res.json()['vested']:
                            if 'tokenId' in v:
                                if v['tokenId'] == "d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413":
                                    tot = v['totalVested'] * .03 # sigusd
                                    totalVested += v['totalVested']
                                    sql = f"""update whitelist set spent_sigusd = {tot!r} where "walletId" = (select id from wallets where address = {wallet!r} limit 1)"""
                                    logging.debug(f'update wallet: {wallet}, spent: {tot}')
                                    logging.debug(sql)
                                    res = con.execute(sql)
                                    # logging.debug(res)
                                    sleep(.1) # give us a chance to break

            except:
                pass

        logging.debug(f'TOTAL VESTED: {totalVested}')
        logging.info(f'sleeping...')
        sleep(POWERNAP)
        i += 1

    except Exception as e:
        logging.debug(e)

