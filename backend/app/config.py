import os

from types import SimpleNamespace
# from base64 import b64encode

# class dotdict(SimpleNamespace):
#     def __init__(self, dictionary, **kwargs):
#         super().__init__(**kwargs)
#         for key, value in dictionary.items():
#             if isinstance(value, dict):
#                 self.__setattr__(key, dotdict(value))
#             else:
#                 self.__setattr__(key, value)

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

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
    'ergopadToken'      : os.getenv('ERGOPAD_TOKEN'),
    'validCurrencies'   : {
      'seedsale' : '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
      'sigusd'   : '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
      'ergopad'  : '5ff2d1cc22ebf959b1cc65453e4ee225b0fdaf4c38a12e3b4ba32ff769bed70f', # 
      # 'sigusd'   : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD
      # 'ergopad'  : '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d', # TODO: need official ergonad token
      # 'kushti' : '??',
      # '$COMET' : '??',
    },
    'connectionString'  : f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
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
    'vestingDuration_1' : 30, # days
    'connectionString'  : f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
  })
}
