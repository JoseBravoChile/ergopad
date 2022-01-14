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
    'jwtSecret'         : os.getenv('JWT_SECRET_KEY'),
    'debug'             : True,
    'validCurrencies'   : {
      'seedsale' : '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
      'sigusd'   : '82d030c7373263c0f048031bfd214d49fea6942a114a291e36120694b4304e9e',
      'ergopad'  : '5ff2d1cc22ebf959b1cc65453e4ee225b0fdaf4c38a12e3b4ba32ff769bed70f', # 
      # 'sigusd'   : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD
      # 'ergopad'  : '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d', # TODO: need official ergonad token
      # 'kushti' : '??',
      # '$COMET' : '??',
    }
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
    'jwtSecret'         : os.getenv('JWT_SECRET_KEY'),
    'debug'             : True,
    'validCurrencies'   : {
      # 'seedsale' : '8eb9a97f4c8e5409ade9a13625f2bbb9f8b081e51d37f623233444743fae8321', # xeed1k
      # 'sigusd'   : '8eb9a97f4c8e5409ade9a13625f2bbb9f8b081e51d37f623233444743fae8321', # xeed1k
      # 'sigusd'   : '29275cf36ffae29ed186df55ac6f8d47b367fe8e398721e200acb71bc32b10a0', # xyzpad
      # 'sigusd'   : '191dd93523e052d9be49680508f675f82e461ef5452d60143212beb42b7f62a8',
      # 'ergopad'  : 'cc3c5dc01bb4b2a05475b2d9a5b4202ed235f7182b46677ed8f40358333b92bb', # xerg10M / TESTING, strategic token
      'ergopad'  : '60def1ed45ffc6493c8c6a576c7a23818b6b2dfc4ff4967e9867e3795886c437', # official
      'sigusd'   : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD (SigmaUSD - V2)
      # 'ergopad'  : 'cc3c5dc01bb4b2a05475b2d9a5b4202ed235f7182b46677ed8f40358333b92bb', # TODO: need official ergopad token
      # 'kushti' : '??',
      # '$COMET' : '??',
    }
  })
}
