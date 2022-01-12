import os

from types import SimpleNamespace
# from base64 import b64encode

class dotdict(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, dotdict(value))
            else:
                self.__setattr__(key, value)

POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USER = os.getenv('POSTGRES_USER')

Network = os.getenv('ERGONODE_NETWORK')
Config = {
  # 'devnet':
  'testnet': dotdict({
    'node'              : os.getenv('ERGONODE_HOST'),
    'explorer'          : 'https://api-testnet.ergoplatform.com/api/v1',
    'assembler'         : 'http://assembler:8080',
    'ergopadNode'       : 'http://ergonode:9052',
    'buyerNode'         : 'http://ergonode2:9052',
    'buyerNode'         : 'http://ergonode2:9053',
    'ergoPlatform'      : 'https://api-testnet.ergoplatform.com/api/v1',
    'ergoWatch'         : 'https://ergo.watch/api/sigmausd/state',
    'coinGecko'         : 'https://api.coingecko.com/api/v3',
    'oraclePool'        : 'https://erg-oracle-ergusd.spirepools.com/frontendData',
    'ergopadTokenId'    : os.getenv('ERGOPAD_TOKENID'),
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'ergopadWallet'     : os.getenv('ERGOPAD_WALLET'),
    'buyerApiKey'       : os.getenv('BUYER_APIKEY'),
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
    'nodeWallet'        : os.getenv('NODE_WALLET'),
    'ergopadToken'      : os.getenv('ERGOPAD_TOKEN'),
    'buyerApiKey'       : os.getenv('BUYER_APIKEY'),
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
    'emailUsername'     : os.getenv('EMAIL_ERGOPAD_USERNAME'),
    'emailPassword'     : os.getenv('EMAIL_ERGOPAD_PASSWORD'),
    'emailSMTP'         : os.getenv('EMAIL_ERGOPAD_SMTP'),
    'emailFrom'         : os.getenv('EMAIL_ERGOPAD_FROM'),
    'minTx'             : 100000, # smallest required for tx
    'txFee'             : 1000000, # min required
    'nanoergsInErg'     : 1000000000, # 1e9
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'vestingPeriods'    : 3,
    'vestingPeriods_1'  : 9,
    'vestingDuration_1' : 30, # days
    'connectionString'  : f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
    'debug'             : True,
  }),
  'mainnet': dotdict({
    'node'              : os.getenv('ERGONODE_HOST'),
    'explorer'          : 'https://api.ergoplatform.com/api/v1',
    'assembler'         : 'http://assembler:8080',
    'buyerNode'         : 'http://ergonode2:9053',
    'ergoWatch'         : 'https://ergo.watch/api/sigmausd/state',
    'coinGecko'         : 'https://api.coingecko.com/api/v3',
    'oraclePool'        : 'https://erg-oracle-ergusd.spirepools.com/frontendData',
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'bogusApiKey'       : os.getenv('BOGUS_APIKEY'),
    'ergopadTokenId'    : os.getenv('ERGOPAD_TOKENID'),
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'ergopadWallet'     : os.getenv('ERGOPAD_WALLET'),
    'buyerApiKey'       : os.getenv('BUYER_APIKEY'),
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
    'ergoPlatform'      : os.getenv('ERGOPLATFORM_HOST'),
    'emailUsername'     : os.getenv('EMAIL_ERGOPAD_USERNAME'),
    'emailPassword'     : os.getenv('EMAIL_ERGOPAD_PASSWORD'),
    'emailSMTP'         : os.getenv('EMAIL_ERGOPAD_SMTP'),
    'emailFrom'         : os.getenv('EMAIL_ERGOPAD_FROM'),
    'minTx'             : 10000000, # required
    'txFee'             : 2000000, # tips welcome
    'nanoergsInErg'     : 1000000000, # 1e9
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'vestingPeriods_1'  : 9,
    'vestingDuration_1' : 30, # days
    'connectionString'  : f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
    'debug'             : True,
  })
}
