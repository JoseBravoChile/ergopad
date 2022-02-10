import requests, json, os
import math
from sqlalchemy import create_engine
from starlette.responses import JSONResponse 
from wallet import Wallet, NetworkEnvironment # ergopad.io library
from config import Config, Network # api specific config
from fastapi import APIRouter, status
from typing import List, Optional
from pydantic import BaseModel
from time import time
from datetime import date, datetime, timezone
from api.v1.routes.asset import get_asset_current_price
from base64 import b64encode, encode
from ergo.updateAllowance import handleAllowance
from ergo.util import encodeLong, encodeLongArray, encodeString, hexstringToB64
import uuid
from hashlib import blake2b
from api.v1.routes.blockchain import getNFTBox, getTokenInfo, getErgoscript, getBoxesWithUnspentTokens
from hashlib import blake2b

staking_router = r = APIRouter()

CFG = Config[Network]
DEBUG = True # CFG.DEBUG
DATABASE = CFG.connectionString

CFG["stakeStateNFT"] = "1daffe65f73b8c2e50e9feca69f4accaa1ef8c4ccd5bfb65a0616fef910bb12b"
CFG["stakePoolNFT"] = "1c93f4621a128471b4b575ae6e3b3324dd73220735acd4116281a597aa588292"
CFG["emissionNFT"] = "1e9f9461d66c16e4715f53f0b4b039966076398d21592f115e2e33692ec0b527"
CFG["stakeTokenID"] =  "1fa30b0b99e01a674b9a09f5ad6ea1c20d0dee000ed6d809538a6eaa961b0be5"
CFG["stakedTokenID"] = "1c30f5cac51947206fb05b69076a0da74788ba7dc5712eb33007c6605f13409f"

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

@r.get("/emit/", name="staking:emit")
def emit():
    stakeStateBox = getNFTBox(CFG.stakeStateNFT)
    stakePoolBox = getNFTBox(CFG.stakePoolNFT)
    emissionBox = getNFTBox(CFG.emissionNFT)

    

class StakeRequest(BaseModel):
    wallet: str
    amount: float
    utxos: List[str]

@r.post("/stake/", name="staking:stake")
async def stake(req: StakeRequest):

    params = {}
    params["stakedTokenID"] = hexstringToB64(CFG.stakedTokenID)
    params["stakePoolNFT"] = hexstringToB64(CFG.stakePoolNFT)
    params["emissionNFT"] = hexstringToB64(CFG.emissionNFT)
    params["stakeStateNFT"] = hexstringToB64(CFG.stakeStateNFT)
    params["stakeTokenID"] = hexstringToB64(CFG.stakeTokenID)

    stakedTokenInfo = getTokenInfo(CFG.stakedTokenID)

    stakeAddress = getErgoscript("stake", params=params)

    stakeStateBox = getNFTBox(CFG.stakeStateNFT)

    tokenAmount = int(req.amount*10**stakedTokenInfo["decimals"])
    
    r4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
    stakeStateOutput = {
        'address': stakeStateBox["address"],
        'value': stakeStateBox["value"],
        'registers': {
            'R4': encodeLongArray([int(r4[0])+tokenAmount,
                    int(r4[1]),
                    int(r4[2])+1,
                    int(r4[3]),
                    int(r4[4])])
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
            'R4': encodeLongArray([int(r4[1]),int(time()*1000)]),
            'R5': encodeString(stakeStateBox["boxId"])
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

    inBoxesRaw = []
    for box in [stakeStateBox["boxId"]]+req.utxos:
        res = requests.get(f'{CFG.ergopadNode}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
        if res.ok:
            inBoxesRaw.append(res.json()['bytes'])
        else:
            return res

    request =  {
            'requests': [stakeStateOutput,stakeOutput,userOutput],
            'fee': int(0.001*nergsPerErg),
            'inputsRaw': inBoxesRaw
        }

    return request

    


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


    emissionAddress = getErgoscript("emission",params=params)

    stakePoolAddress = getErgoscript("stakePool", params=params)

    stakeAddress = getErgoscript("stake",params=params)

    stakeWallet = Wallet(stakeAddress)
    stakeErgoTreeBytes = bytes.fromhex(stakeWallet.ergoTree()[2:])

    stakeHash = b64encode(blake2b(stakeErgoTreeBytes, digest_size=32).digest()).decode('utf-8')

    params["stakeContractHash"] = stakeHash

    stakeStateAddress = getErgoscript("stakeState",params=params)

    stakePoolBox = {
        'address': stakePoolAddress,
        'value': int(0.001*nergsPerErg),
        'registers': {
            'R4': encodeLongArray([int(req.emissionAmount*stakedTokenDecimalMultiplier)])
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
            'R4': encodeLongArray([0,0,0,0,req.cycleDuration_ms])
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
            'R4': encodeLongArray([0,-1,0,req.emissionAmount*stakedTokenDecimalMultiplier])
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

    