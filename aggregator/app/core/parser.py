import ccxt

from argparse import ArgumentParser
from core.config import TIMEFRAMES

parser = ArgumentParser(description='ready, go.')
parser.add_argument('-t', '--timeframe', default='5m',
                    choices=TIMEFRAMES, help='common interval between candles')
parser.add_argument('-s', '--symbol', default='ERG/USDT',
                    help='crypto symbol available on exchange')
parser.add_argument('-x', '--exchange', default='coinex',
                    choices=ccxt.exchanges, help='exchange to gather candles')
parser.add_argument('-l', '--limit', default=1000, type=int,
                    help='exchange to gather candles')
args = parser.parse_args()


EXCHANGE_NAME = args.exchange
SYMBOL = args.symbol
TIMEFRAME = args.timeframe
LIMIT = args.limit
