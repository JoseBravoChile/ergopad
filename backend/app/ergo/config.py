from types import SimpleNamespace
from base64 import b64encode

class dotdict(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, dotdict(value))
            else:
                self.__setattr__(key, value)

Network = 'testnet'
Config = {
  # 'devnet':
  'testnet': dotdict({
    'node'              : 'http://localhost:9054',
    'explorer'          : 'https://api-testnet.ergoplatform.com/api/v1',
    'apiKey'            : 'goalspentchillyamber',
    'assembler'         : 'http://localhost:8080',
    'minTx'             : 10000000, # required
    'txFee'             : 2000000, # tips welcome
    'nanoergsInErg'     : 1000000000, # 1e9
    'nergAmount'        : .1, # default
    'qtyTokens'         : 5, 
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'ergopadWallet'     : '3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw',
    'testingWallet'     : '3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG',
    'ergopadTokenId'    : '81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a',
    'b64ergopadTokenId' : b64encode(bytes.fromhex('81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a')).decode(),
    'requestedTokens'   : 4,
    'vestingPeriods'    : 2,
    'wallet'            : 'http://localhost:9053',
    'walletApiKey'      : 'oncejournalstrangeweather',
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
    'node'              : 'http://localhost:9053',
    'explorer'          : 'https://api.ergoplatform.com/api/v1',
    'apiKey'            : 'helloworld',
    'assembler'         : 'http://localhost:8080',
    'minTx'             : 10000000, # required
    'txFee'             : 2000000, # tips welcome
    'nanoergsInErg'     : 1000000000, # 1e9
    'nergAmount'        : .1, # default
    'qtyTokens'         : 5, 
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'ergopadTokenId'    : '81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a',
    'b64ergopadTokenId' : b64encode(bytes.fromhex('81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a')).decode(),
    'requestedTokens'   : 4,
    'vestingPeriods'    : 2,
    'wallet'            : 'http://localhost:9054',
    'walletApiKey'      : 'xyzpdq',
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
