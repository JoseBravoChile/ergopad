import ccxt
import logging
import numpy as np
import pandas as pd

from core.parser import EXCHANGE_NAME
from core.config import APIKEYS, db


# LOGGING
level = logging.INFO  # TODO: set from .env
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
                    datefmt='%m-%d %H:%M', level=level)


# for xcg in ccxt.exchanges: ...
ACCESS_ID = APIKEYS[EXCHANGE_NAME]['ACCESS_ID']
SECRET_KEY = APIKEYS[EXCHANGE_NAME]['SECRET_KEY']

# exchange = eval(f'ccxt.{exchangeName}()') # alternative using eval
exchange = getattr(ccxt, EXCHANGE_NAME)(
    {'apiKey': ACCESS_ID, 'secret': SECRET_KEY})


def cleanupHistorical(exchange, symbol, timeframes):
    """
    Delete rows older than term
    """
    cleanupAfter = {
        '1m': '3 days',
        '5m': '3 weeks',
        '1d': '3 months',
        '1w': '3 years'
    }

    try:
        for t in timeframes:
            logging.info(f'cleaned timeframe, {t}...')
            tbl = f'{exchange}_{symbol}_{t}'
            sqlCleanup = f"""delete from "{tbl}" where timestamp_utc < CURRENT_DATE - INTERVAL '{cleanupAfter[t]}'"""
            res = db.execute(sqlCleanup, con=db)
            if res.rowcount > 0:
                logging.info(
                    f'cleaned up {res.rowcount} rows in timeframe, {t}...')

    except Exception as e:  # consider narrowing exception handing from generic, "Exception"
        logging.error(
            f'{e}\n{res or ""}\ntable, {tbl} may not exist, sql may be incorrect ({sqlCleanup or ""}), or connection to SQL may be invalid.')
        pass


def getLatestTimestamp(tbl, since='1970-01-01T00:00:00Z', removeLatest=True):
    """
    Find last imported row and remove
    """
    try:
        sqlLatest = f'select max(timestamp_utc) as timestamp_utc from "{tbl}"'
        dfLatest = pd.read_sql(sql=sqlLatest, con=db)

        # from ccxt docs, indicates last close value may be inaccurate
        since = dfLatest.iloc[0]['timestamp_utc']

        # remove latest to avoid dups and provide more accurate closing value
        if removeLatest:
            sqlRemoveLatest = f"""delete from "{tbl}" where timestamp_utc = '{since}'"""
            res = db.execute(sqlRemoveLatest, con=db)
            if res.rowcount == 0:
                logging.warning(
                    'No rows deleted; maybe table is blank, or issue with latest timestamp_utc')

        return exchange.parse8601(since.isoformat())

    except Exception as e:  # consider narrowing exception handing from generic, "Exception"
        logging.error(
            f'table, {tbl} may not exist, or connection to SQL invalid.')
        pass

    return 0


def getLatestOHLCV(exchange, symbol, since=None):
    """
    Find the latest X rows of ohlcv data from exchange and save to SQL
    """
    data = []
    limit = 1000
    timeframe = '5m'
    tf_milliseconds = 5*60*1000
    try:
        if exchange.has['fetchOHLCV']:
            # paginate latest ohlcv from exchange
            if since == None:
                since = exchange.milliseconds() - 86400000  # 1 day

            while since < exchange.milliseconds()-tf_milliseconds:
                print(f'since: {since}...')
                data += exchange.fetch_ohlcv(symbol,
                                             timeframe=timeframe, since=since, limit=limit)
                since = int(data[len(data)-1][0])

    except Exception as e:
        logging.debug(e)

    return data


def putLatestOHLCV(ohlcv, tbl, utcLatest):
    """
    comments go here
    """
    try:
        # save ohlcv to sql
        columns = ['timestamp_utc', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(np.row_stack(ohlcv), columns=columns)
        dfLatest = df[df['timestamp_utc'] >= utcLatest].astype(
            {'timestamp_utc': 'datetime64[ms]'}).set_index('timestamp_utc')
        dfLatest.to_sql(tbl, con=db, if_exists='append',
                        index_label='timestamp_utc')

    except Exception as e:
        logging.debug(e)
