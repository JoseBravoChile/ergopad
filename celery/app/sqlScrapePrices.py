from celery import Celery
from kombu import Queue, Exchange
# from celery.schedules import crontab
from os import getenv

celery = Celery("tasks"
    , broker="redis://redis:6379/0" # broker queue managed here
    , backend = 'redis://redis:6379/0' # results are stored here
)

#region LOGGING
import logging
DEBUG = True
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region ROUTING
# https://www.distributedpython.com/2018/05/29/task-routing/
# celery.conf.task_routes = {"tasks.*": "task-queue"}

# celery worker -E -l INFO -n workerA -Q for_task_A
# celery worker -E -l INFO -n workerB -Q for_task_B
CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('for_task_A', Exchange('for_task_A'), routing_key='for_task_A'),
    Queue('for_task_B', Exchange('for_task_B'), routing_key='for_task_B'),
)

CELERY_ROUTES = {
    'my_taskA': {'queue': 'for_task_A', 'routing_key': 'for_task_A'},
    'my_taskB': {'queue': 'for_task_B', 'routing_key': 'for_task_B'},
}

celery.conf.task_default_queue = 'default'
# celery.conf.task_default_exchange_type = 'direct'
celery.conf.task_default_routing_key = 'default'

# celery.conf.beat_schedule = {
#     'test-task': {
#         'task': 'tasks.hello',
#         'schedule': crontab(minute=0, hour='*/3'),
#         'options': {'exchange': 'for_task_A'}
#     },
# }
#endregion ROUTING

connErgopad = f"postgresql://{getenv('POSTGRES_USER')}:{getenv('POSTGRES_PASSWORD')}@{getenv('POSTGRES_HOST')}:{getenv('POSTGRES_PORT')}/{getenv('POSTGRES_DBNM')}",
ergo_watch_api: str = 'https://ergo.watch/api/sigmausd/state'

def backoff(attempts):
    return 2**attempts

@celery.task (bind=True, default_retry_delay=300, max_retries=5)
def hello(self, word: str) -> str:
    # celery = Celery('jt', broker='redis://10.0.0.134:6379/0', backend='redis://10.0.0.134:6379/0')
    # res = celery.send_task('sqlScrapePrices.hello', ['world'], queue='default')
    # celery.conf.task_routes = {'sqlScrapePrices.hello': {'queue': 'default'}}
    try:
        return {"Hello": word}
    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

@celery.task(acks_late=True, bind=True, default_retry_delay=300, max_retries=5)
def scrapePriceData():
    try:
        # SigUSD/SigRSV
        logging.debug('get sigUSD/RSV from ergowatch')
        res = requests.get(ergo_watch_api).json()
        if res.ok:
            logging.debug('got ergowatch result')
            sigUsdPrice = 1/(res['peg_rate_nano']/nerg2erg)
            circ_sigusd_cents = res['circ_sigusd']/100.0 # given in cents
            peg_rate_nano = res['peg_rate_nano'] # also SigUSD
            reserves = res['reserves'] # total amt in reserves (nanoerg)
            liabilities = min(circ_sigusd_cents * peg_rate_nano, reserves) # lower of reserves or SigUSD*SigUSD_in_circulation
            equity = reserves - liabilities # find equity, at least 0
            if equity < 0: equity = 0
            if res['circ_sigrsv'] <= 1:
                sigRsvPrice = 0.0
            else:
                sigRsvPrice = equity/res['circ_sigrsv']/nerg2erg # SigRSV      
            tbl = 'ergowatch_ERG/sigUSD/sigRSV_continuous_5m'
            con = psycopg.connect(connErgopad)
            logging.debug(f'write to {tbl}: {sigUsdPrice}sigUSD, {sigRsvPrice}sigRSV')
            with con.cursor().copy(f"""copy "{tbl}" ('timestamp_utc', 'sigUSD', 'sigRSV') from STDIN""") as cpy:
                cpy.write_row([int(time()), sigUsdPrice, sigRsvPrice])
        else:
            logging.error(f'did not receive valid data from: {ergo_watch_api}')

    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

@celery.task(acks_late=True, bind=True, default_retry_delay=300, max_retries=5)
def cleanupHistorical(exchange, symbol, timeframes):
    """ Delete rows older than term """
    cleanupAfter = {
        '1m': '3 days',
        '5m': '3 weeks',
        '1d': '3 months',
        '1w': '3 years'
    }

    try:
        con = psycopg.connect(connErgopad)
        for t in timeframes:
            logging.info(f'cleaned timeframe, {t}...')
            sqlCleanup = f"""delete from "{exchange}_{symbol}_{t}" where timestamp_utc < CURRENT_DATE - INTERVAL '{cleanupAfter[t]}'"""
            res = con.execute(sqlCleanup)
            if res.rowcount > 0:
                logging.info(f'cleaned up {res.rowcount} rows in timeframe, {t}...')

    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

@celery.task(acks_late=True, bind=True, default_retry_delay=300, max_retries=5)
def putLatestOHLCV(ohlcv, tbl):
    """ comments go here """
    try:
        con = psycopg.connect(connErgopad)
        with con.cursor().copy(f"""copy "{tbl}" ('timestamp_utc', 'open', 'high', 'low', 'close', 'volume') from STDIN""") as cpy:
            for r in ohlcv:
                cpy.write_row(r)

    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

