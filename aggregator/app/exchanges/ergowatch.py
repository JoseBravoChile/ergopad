from time import time
import pandas as pd
import logging
import requests

from core.config import db

# LOGGING
level = logging.INFO  # TODO: set from .env
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
                    datefmt='%m-%d %H:%M', level=level)


def getSigErgo():
    """
    TODO: convet to OHLC from ergo.watch, or query oracle pools directly
    """
    # total_sigrsv = 100000000000.01 # initial amount SigRSV
    # default_rsv_price = 1000000 # lower bound/default SigRSV value
    nerg2erg = 1000000000.0  # 1e9 satoshis/kushtis in 1 erg

    # ergo_platform_url: str = 'https://api.ergoplatform.com/api/v1'
    ergo_watch_api: str = 'https://ergo.watch/api/sigmausd/state'
    # oracle_pool_url: str = 'https://erg-oracle-ergusd.spirepools.com/frontendData'
    # coingecko_url: str = 'https://api.coingecko.com/api/v3' # coins/markets?vs_currency=usd&ids=bitcoin"

    # SigUSD/SigRSV
    res = requests.get(ergo_watch_api).json()
    if res:
        sigUsdPrice = 1/(res['peg_rate_nano']/nerg2erg)
        circ_sigusd_cents = res['circ_sigusd']/100.0  # given in cents
        peg_rate_nano = res['peg_rate_nano']  # also SigUSD
        reserves = res['reserves']  # total amt in reserves (nanoerg)
        # lower of reserves or SigUSD*SigUSD_in_circulation
        liabilities = min(circ_sigusd_cents * peg_rate_nano, reserves)
        equity = reserves - liabilities  # find equity, at least 0
        if equity < 0:
            equity = 0
        if res['circ_sigrsv'] <= 1:
            sigRsvPrice = 0.0
        else:
            sigRsvPrice = equity/res['circ_sigrsv']/nerg2erg  # SigRSV

        df = pd.DataFrame({'timestamp_utc': [int(time())], 'sigUSD': [
                          sigUsdPrice], 'sigRSV': [sigRsvPrice]}).set_index('timestamp_utc')
        df.to_sql('ergowatch_ERG/sigUSD/sigRSV_continuous_5m', con=db,
                  if_exists='append', index_label='timestamp_utc')
    else:
        logging.error(f'did not receive valid data from: {ergo_watch_api}')
