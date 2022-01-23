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
from ergo.util import encodeLong, encodeString
import uuid
from hashlib import blake2b
from api.v1.routes.blockchain import getTokenInfo, getErgoscript, getBoxesWithUnspentTokens
from hashlib import blake2b

staking_router = r = APIRouter()

CFG = Config[Network]
DEBUG = True # CFG.DEBUG
DATABASE = CFG.connectionString

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
    params["stakedTokenID"] = req.stakedTokenID
    params["stakePoolNFT"] = req.stakePoolNFT
    params["emissionNFT"] = req.emissionNFT
    params["stakeStateNFT"] = req.stakeStateNFT
    params["stakeTokenID"] = req.stakeTokenID

    stakeStateAddress = getErgoscript("stakeState",params=params)

    logging.info(stakeStateAddress)

    stakeStateWallet = Wallet(stakeStateAddress)
    stakeStateErgoTreeBytes = stakeStateWallet.addrBytes[:len(stakeStateWallet.addrBytes) - 4]

    logging.info(stakeStateErgoTreeBytes)

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
            'address': getErgoscript('alwaysTrue'),
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

    