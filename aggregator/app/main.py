import logging
from time import sleep

from core.config import POWERNAP, TIMEFRAMES, SYMBOLS
from core.parser import EXCHANGE_NAME, LIMIT
from exchanges.coinex import exchange, getLatestTimestamp, putLatestOHLCV, cleanupHistorical
from exchanges.ergowatch import cleanupHistoricalErgoWatch, getSigErgo
from exchanges.ergodex import cleanupHistoricalErgodex, getErgodexToken


# NOTES
"""
Read OHLCV+ data from exchange and store in database.  The data will be created if it 
does not exist, otherwise appended.  Each exchange/symbol will have it's own table since
this is likely to be called async and from a celery worker.

TODO: ability to include exchange as column to be able to store multi symbols same table
TODO: automate with CLI params; call from celery workers
TODO: to use async, must include await methods
TODO: move to crontab?

Helpers:
----------
find symbols with string
> list(filter(None, [m if (m.find('ERG') != -1) else None for m in ccxt.hitbtc().load_markets()]))

get symbol in form for database
> pd.DataFrame.from_dict(ccxt.hitbtc().fetch_symbol('ERG/BTC'), orient='index').drop('info').T

if pulling from symbol, can use this to format as dataframe
> df = pd.DataFrame.from_dict(exchange.fetch_symbol(symbol), orient='index')
> df = df.drop('info') # ignore
> df.T.to_sql(tbl, con=con, if_exists='append') # transpose dataframe with default cols from ccxt

Initial:
---------
frm = exchange.parse8601('2021-10-20 00:00:00')
now = exchange.milliseconds()
symbol = 'ERG/USDT'
data = []
msec = 1000
minute = 60 * msec
hold = 30

while from_timestamp < now:
    try:
        print(exchange.milliseconds(), 'Fetching candles starting from', exchange.iso8601(from_timestamp))
        ohlcvs = exchange.fetch_ohlcv(symbol, '1m', from_timestamp)
        print(exchange.milliseconds(), 'Fetched', len(ohlcvs), 'candles')
        from_timestamp = ohlcvs[-1][0]
        data += ohlcvs
    except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:
        print('Got an error', type(error).__name__, error.args, ', retrying in', hold, 'seconds...')
        time.sleep(hold)

"""

# LOGGING
level = logging.INFO  # TODO: set from .env
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
                    datefmt='%m-%d %H:%M', level=level)


# MAIN
if (__name__ == '__main__'):
    # seconds in timeframe
    polling = {
        '1m': 1,
        '5m': 5,
        '1d': 1440,
        '1w': 10080,
    }

    i = 0
    # Save to local database
    while True:
        try:
            # cctx
            for symbol in SYMBOLS:
                # OHLCV for these coins
                for timeframe in TIMEFRAMES:
                    if i % polling[timeframe] == 0:
                        logging.info(
                            f'{EXCHANGE_NAME}.{symbol} polling for timeframe: {timeframe}')
                        # destination
                        tbl = f'{EXCHANGE_NAME}_{symbol}_{timeframe}'
                        # get latest timestamp; remove from table, if exists
                        logging.debug(f'get {tbl}...')
                        since = getLatestTimestamp(tbl)
                        # get lastest X OHLCV
                        # ohlcv = getLatestOHLCV(exchange, symbol) # TODO: pagination
                        logging.debug(f'fetch {symbol}...')
                        # coinex buggy with, "since" -hack
                        ohlcv = exchange.fetch_ohlcv(
                            symbol, timeframe=timeframe, since=since, limit=LIMIT)
                        # save most recent OHLCV to SQL
                        logging.debug(f'put {since}...')
                        putLatestOHLCV(ohlcv, tbl, since)

                # cleanup daily
                if i % polling['1d'] == 0:
                    logging.debug(f'cleanup...')
                    cleanupHistorical(EXCHANGE_NAME, symbol, TIMEFRAMES)

            # sigUSD/sigRSV
            if i % polling['5m'] == 0:
                logging.info(
                    f'ergo.sigUSD/sigRSV polling for timeframe: 5m')
                getSigErgo()

            # ergodex
            if i % polling['5m'] == 0:
                logging.info(
                    f'ergodex.ERG/token polling for timeframe: 5m'
                )
                getErgodexToken()

            # cleanup daily
            if i % polling['1d'] == 0:
                logging.debug(f'cleanup... ergodex and ergowatch')
                cleanupHistoricalErgoWatch()
                cleanupHistoricalErgodex()

            # polling interval
            logging.info(f'sleep for {POWERNAP}s...\n')
            i = i + 1
            sleep(POWERNAP)  # seconds

        except Exception as e:
            logging.error(e)
            pass
