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
    'explorer'          : 'https://api-testnet.ergoplatform.com/api/v1',
    'assembler'         : 'http://assembler:8080',
    'minTx'             : 100000, # smallest required for tx
    'txFee'             : 1000000, # min required
    'nanoergsInErg'     : 1000000000, # 1e9
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'ergopadTokenId'    : os.getenv('ERGOPAD_TOKENID'),
    'node'              : 'http://ergonode:9052',
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'ergopadWallet'     : os.getenv('ERGOPAD_WALLET'),
    'ergopadNode'       : 'http://ergonode:9052',
    'buyerApiKey'       : os.getenv('BUYER_APIKEY'),
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
    'buyerNode'         : 'http://ergonode2:9052',
    'vestingPeriods'    : 3,
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
    'nodeWallet'        : os.getenv('NODE_WALLET'),
    'seedSaleToken'     : os.getenv('SEED_SALE_TOKEN'),
    'ergopadToken'      : os.getenv('ERGOPAD_TOKEN')
  }),
  'mainnet': dotdict({
    'node'              : os.getenv('ERGONODE_HOST'),
    'explorer'          : 'https://api.ergoplatform.com/api/v1',
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'bogusApiKey'       : os.getenv('BOGUS_APIKEY'),
    'assembler'         : 'http://assembler:8080',
    'minTx'             : 10000000, # required
    'txFee'             : 2000000, # tips welcome
    'nanoergsInErg'     : 1000000000, # 1e9
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'ergopadTokenId'    : os.getenv('ERGOPAD_TOKENID'),
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'ergopadWallet'     : os.getenv('ERGOPAD_WALLET'),
    'buyerApiKey'       : os.getenv('BUYER_APIKEY'),
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
    'buyerNode'         : 'http://ergonode2:9053',
    'vestingPeriods_1'  : 9,
    'vestingDuration_1' : 30 # days
  })
}
