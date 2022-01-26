import requests, json, os
import math
from sqlalchemy import create_engine
from starlette.responses import JSONResponse 
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, status
from typing import Optional
from pydantic import BaseModel
from time import time
from datetime import date, datetime, timezone
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode, encode
from ergo.updateAllowance import handleAllowance
from ergo.util import encodeLong, encodeString, hexstringToB64
import uuid
from hashlib import blake2b
from api.v1.routes.blockchain import getNFTBox, getTokenInfo, getErgoscript, getBoxesWithUnspentTokens
from hashlib import blake2b

staking_router = r = APIRouter()

CFG = Config[Network]
DEBUG = True # CFG.DEBUG
DATABASE = CFG.connectionString

CFG["stakeStateNFT"] = "174f8bc88320897763f79e5da5e088043ca2db95df63eb68cf0edd9eeb3b3d74"
CFG["stakePoolNFT"] = "17da70ae8ecc814f6bf04262a0f247b8efc2bf765d016e36072ea9b200ddcf17"
CFG["emissionNFT"] = "18f2d72eaf1821142c0b5f2f7a8e95775dfbc34a2ae9af0be6ad7d630d2db6e2"
CFG["stakeTokenID"] =  "19a1cba03bb9b5416a42a5c5e95d4db0bc9790ebde480c2538cf7c2bc8949f0f"
CFG["stakedTokenID"] = "129804369cc01c02f9046b8f0e37f8fc924e71b64652a0a331e6cd3c16c1f028"

nergsPerErg        = 1000000000
headers            = {'Content-Type': 'application/json'}

duration_ms = {
    'month': 365*24*60*60*1000/12,
    'week': 7*24*60*60*1000,
    'day': 24*60*60*1000,
    'minute': 60*1000
}

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

class StakeRequest(BaseModel):
    wallet: str
    amount: float

@r.post("/stake/", name="staking:stake")
async def stake(req: StakeRequest):

    params = {}
    params["stakedTokenID"] = hexstringToB64(CFG.stakedTokenID)
    params["stakePoolNFT"] = hexstringToB64(CFG.stakePoolNFT)
    params["emissionNFT"] = hexstringToB64(CFG.emissionNFT)
    params["stakeStateNFT"] = hexstringToB64(CFG.stakeStateNFT)
    params["stakeTokenID"] = hexstringToB64(CFG.stakeTokenID)

    stakedTokenInfo = getTokenInfo(CFG.stakedTokenID)

    stakeStateAddress = getErgoscript("stakeState",params=params)

    logging.info(stakeStateAddress)

    stakeStateWallet = Wallet(stakeStateAddress)
    stakeStateErgoTreeBytes = bytes.fromhex(stakeStateWallet.ergoTree()[2:])

    logging.info(stakeStateWallet.ergoTree()[2:])

    stakeStateHash = b64encode(blake2b(stakeStateErgoTreeBytes, digest_size=32).digest()).decode('utf-8')
    params["stakeStateContractHash"] = stakeStateHash

    stakeAddress = getErgoscript("stake", params=params)

    stakeWallet = Wallet(stakeAddress)
    stakeErgoTreeBytes = bytes.fromhex(stakeWallet.ergoTree()[2:])

    logging.info(stakeErgoTreeBytes)

    stakeHash = b64encode(blake2b(stakeErgoTreeBytes, digest_size=32).digest()).decode('utf-8')
    params["stakeContractHash"] = stakeHash
    params["buyerWallet"] = req.wallet
    params["timestamp"] = int(time())

    #preStakeAddress = getErgoscript("preStake", params=params)
    preStakeAddress = getErgoscript("alwaysTrue", params=params)

    stakeStateBox = getNFTBox(CFG.stakeStateNFT)

    tokenAmount = int(req.amount*10**stakedTokenInfo["decimals"])

    stakeStateOutput = {
        'address': stakeStateAddress,
        'value': stakeStateBox["value"],
        'registers': {
            'R4': encodeLong(int(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])+tokenAmount),
            'R5': stakeStateBox["additionalRegisters"]["R5"]["serializedValue"],
            'R6': encodeLong(int(stakeStateBox["additionalRegisters"]["R6"]["renderedValue"])+1),
            'R7': stakeStateBox["additionalRegisters"]["R7"]["serializedValue"],
            'R8': stakeStateBox["additionalRegisters"]["R8"]["serializedValue"],
        },
        'assets': [
            {
                'tokenId': stakeStateBox["assets"][0]["tokenId"],
                'amount': stakeStateBox["assets"][0]["amount"]
            },
            {
                'tokenId': stakeStateBox["assets"][1]["tokenId"],
                'amount': stakeStateBox["assets"][1]["amount"]-1
            }
        ]
    }

    stakeOutput = {
        'address': stakeAddress,
        'value': int(0.001*nergsPerErg),
        'registers': {
            'R4': stakeStateBox["additionalRegisters"]["R5"]["serializedValue"],
            'R5': encodeString(stakeStateBox["boxId"]),
            'R6': encodeLong(int(time()*1000))
        },
        'assets': [
            {
                'tokenId': stakeStateBox["assets"][1]["tokenId"],
                'amount': 1
            },
            {
                'tokenId': CFG.stakedTokenID,
                'amount': tokenAmount
            }
        ]
    }

    userOutput = {
        'address': req.wallet,
        'ergValue': int(0.008*nergsPerErg),
        'amount': 1,
        'name': f'{stakedTokenInfo["name"]} Stake Key {datetime.now()}',
        'description': f'Stake key to be used for unstaking {stakedTokenInfo["name"]}',
        'decimals': "0"
    }

    request = {
        'address': preStakeAddress,
        'returnTo': req.wallet,
        'startWhen': {
            'erg': int(0.01*nergsPerErg),
            CFG.stakedTokenID: int(req.amount*10**stakedTokenInfo["decimals"])
        },
        'txSpec': {
            'requests': [stakeStateOutput,stakeOutput,userOutput],
            'fee': int(0.001*nergsPerErg),
            'inputs': [stakeStateBox["boxId"],'$userIns'],
            'dataInputs': []
        }
    }

    # don't bonk if can't jsonify request
    try: logging.info(f'request: {json.dumps(request)}')
    except: pass

    # logging.info(f'build request: {request}')
    # logging.info(f'\n::REQUEST::::::::::::::::::\n{json.dumps(request)}\n::REQUEST::::::::::::::::::\n')

    # make async request to assembler
    res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)    
    logging.debug(res.content)
    assemblerId = res.json()['id']
    fin = requests.get(f'{CFG.assembler}/result/{assemblerId}')
    logging.info({'status': 'success', 'fin': fin.json(), 'followId': assemblerId})

    


class BootstrapRequest(BaseModel):
    stakeStateNFT: str
    stakePoolNFT: str
    emissionNFT: str
    stakeTokenID: str
    stakedTokenID: str
    stakeAmount: int
    emissionAmount: int
    cycleDuration_ms: int

# bootstrap staking setup
@r.post("/bootstrap/", name="staking:bootstrap")
async def bootstrapStaking(req: BootstrapRequest):

    stakedToken = getTokenInfo(req.stakedTokenID)
    stakedTokenDecimalMultiplier = 10**stakedToken["decimals"]
    stakeStateNFT = getTokenInfo(req.stakeStateNFT)

    if (stakeStateNFT["name"] != f'{stakedToken["name"]} Stake State'):
        return({"success": False, "Error": f"Wrong name for stake state NFT {stakeStateNFT['name']}"})
    if (stakeStateNFT["emissionAmount"]>1):
        return({"success": False, "Error": f"There should only be one {stakeStateNFT['name']}"})

    stakePoolNFT = getTokenInfo(req.stakePoolNFT)

    if (stakePoolNFT["name"] != f'{stakedToken["name"]} Stake Pool'):
        return({"success": False, "Error": f"Wrong name for stake pool NFT {stakePoolNFT['name']}"})
    if (stakePoolNFT["emissionAmount"]>1):
        return({"success": False, "Error": f"There should only be one {stakePoolNFT['name']}"})

    emissionNFT = getTokenInfo(req.emissionNFT)

    if (emissionNFT["name"] != f'{stakedToken["name"]} Emission'):
        return({"success": False, "Error": f"Wrong name for emission NFT {emissionNFT['name']}"})
    if (emissionNFT["emissionAmount"]>1):
        return({"success": False, "Error": f"There should only be one {emissionNFT['name']}"})

    stakeTokenID = getTokenInfo(req.stakeTokenID)

    if (stakeTokenID["name"] != f'{stakedToken["name"]} Stake Token'):
        return({"success": False, "Error": f"Wrong name for stake token {stakeTokenID['name']}"})
    if (stakeTokenID["emissionAmount"]<1000000000):
        return({"success": False, "Error": f"There should only be at least a billion {stakeTokenID['name']}"})

    params = {}
    params["stakedTokenID"] = hexstringToB64(req.stakedTokenID)
    params["stakePoolNFT"] = hexstringToB64(req.stakePoolNFT)
    params["emissionNFT"] = hexstringToB64(req.emissionNFT)
    params["stakeStateNFT"] = hexstringToB64(req.stakeStateNFT)
    params["stakeTokenID"] = hexstringToB64(req.stakeTokenID)
    params["timestamp"] = int(time())

    stakeStateAddress = getErgoscript("stakeState",params=params)

    logging.info(stakeStateAddress)

    stakeStateWallet = Wallet(stakeStateAddress)
    stakeStateErgoTreeBytes = bytes.fromhex(stakeStateWallet.ergoTree()[2:])

    logging.info(stakeStateWallet.ergoTree()[2:])

    stakeStateHash = b64encode(blake2b(stakeStateErgoTreeBytes, digest_size=32).digest()).decode('utf-8')
    params["stakeStateContractHash"] = stakeStateHash

    emissionAddress = getErgoscript("emission",params=params)

    stakePoolAddress = getErgoscript("stakePool", params=params)

    stakePoolBox = {
        'address': stakePoolAddress,
        'value': int(0.001*nergsPerErg),
        'registers': {
            'R4': encodeLong(int(req.emissionAmount*stakedTokenDecimalMultiplier))
        },
        'assets': [
            {
                'tokenId': req.stakePoolNFT,
                'amount': 1
            },
            {
                'tokenId': req.stakedTokenID,
                'amount': req.stakeAmount*stakedTokenDecimalMultiplier
            }
        ]
    }

    stakeStateBox = {
        'address': stakeStateAddress,
        'value': int(0.001*nergsPerErg),
        'registers': {
            'R4': encodeLong(int(0)),
            'R5': encodeLong(int(0)),
            'R6': encodeLong(int(0)),
            'R7': encodeLong(int(0)),
            'R8': encodeLong(req.cycleDuration_ms)
        },
        'assets': [
            {
                'tokenId': req.stakeStateNFT,
                'amount': 1
            },
            {
                'tokenId': req.stakeTokenID,
                'amount': 1000000000
            }
        ]
    }

    emissionBox = {
        'address': emissionAddress,
        'value': int(0.001*nergsPerErg),
        'registers': {
            'R4': encodeLong(int(0)),
            'R5': encodeLong(int(0)),
            'R6': encodeLong(int(0)),
            'R7': encodeLong(req.emissionAmount*stakedTokenDecimalMultiplier)
        },
        'assets': [
            {
                'tokenId': req.emissionNFT,
                'amount': 1
            }
        ]
    }

    inputs = set()

    for boxId in getBoxesWithUnspentTokens(tokenId=req.emissionNFT,tokenAmount=1).keys():
        inputs.add(boxId)
    for boxId in getBoxesWithUnspentTokens(tokenId=req.stakeStateNFT,tokenAmount=1).keys():
        inputs.add(boxId)
    for boxId in getBoxesWithUnspentTokens(tokenId=req.stakePoolNFT,tokenAmount=1).keys():
        inputs.add(boxId)
    for boxId in getBoxesWithUnspentTokens(tokenId=req.stakedTokenID,tokenAmount=req.stakeAmount*stakedTokenDecimalMultiplier).keys():
        inputs.add(boxId)
    for boxId in getBoxesWithUnspentTokens(tokenId=req.stakeTokenID,tokenAmount=1000000000).keys():
        inputs.add(boxId)

    request = {
            'address': getErgoscript('alwaysTrue',params=params),
            'returnTo': CFG.ergopadWallet,
            'startWhen': {
                'erg': 0, 
            },
            'txSpec': {
                'requests': [stakePoolBox,stakeStateBox,emissionBox],
                'fee': int(0.001*nergsPerErg),          
                'inputs': list(inputs),
                'dataInputs': [],
            },
        }

    logging.debug(request)
    res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)   
    logging.debug(res.content)

    return({"success": True})

    