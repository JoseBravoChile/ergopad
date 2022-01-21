import requests, json, os
from sqlalchemy import create_engine
from starlette.responses import JSONResponse 
from time import time, sleep
from datetime import date, datetime, timezone

import logging
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=logging.DEBUG)

import inspect
myself = lambda: inspect.stack()[1][3]

POWERNAP = 15 # s to sleep for infinite loop
DATABASE = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}"
ASSEMBLER = 'http://assembler:8080'

while True:
    try:
        con = create_engine(DATABASE)
        sql = f"""
            select "assemblerId", "assemblerStatus", "walletAddress"
            from purchases
            where id > 0
                and "assemblerStatus" not in ('success', 'timeout')
        """
        logging.debug(sql)
        res = con.execute(sql).fetchall()
        logging.debug(res)

        for r in res:
            wallet = r['walletAddress']
            logging.debug(f"assemblerId: {r['assemblerId']}")
            res = requests.get(f"{ASSEMBLER}/result/{r['assemblerId']}")
            if res.ok:
                detail = res.json()['detail']
                status = r['assemblerStatus']
                assmid = r['assemblerId']
                logging.info(f"update followId:{assmid} to staus:{detail}")
                if status != detail:
                    try:
                        sql = f"""
                            update purchases
                                set "assemblerStatus" = {detail!r} 
                            where "assemblerId" = {assmid!r}
                        """
                        logging.debug(sql)
                        res = con.execute(sql)
                    except:
                        pass

            else:
                logging.info(f"issue with followId:{r['assemblerId']}--{res.content}")

        logging.info(f'sleeping...')
        sleep(POWERNAP)

    except Exception as e:
        logging.debug(e)

