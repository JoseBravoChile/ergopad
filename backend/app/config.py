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

class Stopwatch(object):
    def __init__(self):
        self.start_time = None
        self.stop_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.stop_time = time.time()

    @property
    def time_elapsed(self):
        return time.time() - self.start_time

    @property
    def total_run_time(self):
        return self.stop_time - self.start_time

    def __enter__(self):
        self.start()
        return self

    def __exit__(self):
        self.stop()

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
    'nodeWallet'        : os.getenv('ERGOPAD_WALLET'),
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
      'seedsale'        : '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d',
      # 'seedsale'        : '129804369cc01c02f9046b8f0e37f8fc924e71b64652a0a331e6cd3c16c1f028',
      'strategic_sale'  : 'e403836f51838b949c05cd4ab221ba3e004bddc9b5af4025c39031bb8853dc43',
      'sigusd'          : '931aadfacfdde2849a7353472910b2e5e56f5b6f8f2be92859a7ff61d0bf9948',
      # 'ergopad'         : '58c6125991977ab70fe84869e379f508bf03f81517b1e6c66c2267247eb30915', # 
      'ergopad'         : '129804369cc01c02f9046b8f0e37f8fc924e71b64652a0a331e6cd3c16c1f028', # 
      # 'sigusd'   : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD
      # 'ergopad'  : '0890ad268cd62f29d09245baa423f2251f1d77ea21443a27d60c3c92377d2e4d', # TODO: need official ergonad token
      # 'kushti' : '??',
      # '$COMET' : '??',
    }
  }),
  'mainnet': dotdict({
    'node'              : os.getenv('ERGONODE_HOST'),
    'explorer'          : 'https://api.ergoplatform.com/api/v1',
    'ergoPlatform'      : 'https://api.ergoplatform.com/api/v1',
    'assembler'         : 'http://assembler:8080',
    'ergopadNode'       : 'http://ergonode:9053',
    'buyerNode'         : 'http://ergonode2:9053',
    'ergoWatch'         : 'https://ergo.watch/api/sigmausd/state',
    'coinGecko'         : 'https://api.coingecko.com/api/v3',
    'oraclePool'        : 'https://erg-oracle-ergusd.spirepools.com/frontendData',
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'bogusApiKey'       : os.getenv('BOGUS_APIKEY'),
    'nodeWallet'        : os.getenv('ERGOPAD_WALLET'),
    'ergopadTokenId'    : os.getenv('ERGOPAD_TOKENID'),
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'ergopadWallet'     : os.getenv('ERGOPAD_WALLET'),
    'buyerApiKey'       : os.getenv('BUYER_APIKEY'),
    'buyerWallet'       : os.getenv('BUYER_WALLET'),
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
      'seedsale'        : '02203763da5f27c01ba479c910e479c4f479e5803c48b2bf4fd4952efa5c62d9',
      'strategic_sale'  : '60def1ed45ffc6493c8c6a576c7a23818b6b2dfc4ff4967e9867e3795886c437',
      # 'ergopad'         : 'cc3c5dc01bb4b2a05475b2d9a5b4202ed235f7182b46677ed8f40358333b92bb',
      'ergopad'         : 'd71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413', # official
      'sigusd'          : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD (SigmaUSD - V2)
    }
  })
}
