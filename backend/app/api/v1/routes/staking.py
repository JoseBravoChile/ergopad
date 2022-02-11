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
from api.v1.routes.blockchain import getNFTBox, getTokenBoxes, getTokenInfo, getErgoscript, getBoxesWithUnspentTokens
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

week = 1000*60*60*24*7

class UnstakeRequest(BaseModel):
    stakeBox: str
    amount: float
    utxos: List[str]

@r.post("/unstake/", name="staking:unstake")
async def unstake(req: UnstakeRequest):

    stakeStateBox = getNFTBox(CFG.stakeStateNFT)

    res = requests.get(f'{CFG.explorer}/boxes/{req.stakeBox}')

    if res.ok:
        stakeBox = res.json()
        currentTime = int(time()*1000)
        amountToUnstake = min(int(req.amount*10**2),stakeBox["assets"][1]["amount"])
        stakeBoxR4 = eval(stakeBox["additionalRegisters"]["R4"]["renderedValue"])
        stakeTime = stakeBoxR4[1] 
        userBox = getNFTBox(stakeBox["additionalRegisters"]["R5"]["renderedValue"])
        timeStaked = currentTime - stakeTime
        weeksStaked = int(timeStaked/week)
        penalty = 0 if (weeksStaked > 8) else amountToUnstake*5/100  if (weeksStaked > 6) else amountToUnstake*125/1000 if (weeksStaked > 4) else amountToUnstake*20/100 if (weeksStaked > 2) else amountToUnstake*25/100
        partial = amountToUnstake < stakeBox["assets"][1]["amount"]
        stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
        outputs = []
        outputs.append({
            'address': stakeStateBox["address"],
            'value': stakeStateBox["value"],
            'assets': [
                {
                    'tokenId': CFG.stakeStateNFT,
                    'amount': 1
                },
                {
                    'tokenId': CFG.stakeTokenID,
                    'amount': stakeStateBox["assets"][1]["amount"] if (partial) else stakeStateBox["assets"][1]["amount"]+1
                }
            ],
            'registers': {
                'R4': encodeLongArray([
                    stakeStateR4[0]-amountToUnstake,
                    stakeStateR4[1],
                    stakeStateR4[2] - (0 if (partial) else 1),
                    stakeStateR4[3],
                    stakeStateR4[4]
                ])
            }
        })
        outputs.append({
            'value': int(0.001*nergsPerErg),
            'address': userBox["address"],
            'assets': [
                {
                    'tokenId': CFG.stakedTokenID,
                    'amount': amountToUnstake-penalty
                },
                {
                    'tokenId': stakeBox["additionalRegisters"]["R5"]["renderedValue"],
                    'amount': 1
                }
            ] if (partial) else [
                {
                    'tokenId': CFG.stakedTokenID,
                    'amount': amountToUnstake-penalty
                }
            ]
        })
        assetsToBurn = []
        if partial:
            outputs.append(
                {
                    'value': stakeBox["value"],
                    'address': stakeBox["address"],
                    'assets': [
                        {
                            'tokenId': CFG.stakeTokenID,
                            'amount': 1
                        },
                        {
                            'tokenId': CFG.stakedTokenID,
                            'amount': stakeBox["assets"][1]["amount"]-amountToUnstake
                        }
                    ],
                    "registers": {
                        'R4': stakeBox["additionalRegisters"]["R4"]["serializedValue"],
                        'R5': stakeBox["additionalRegisters"]["R5"]["serializedValue"]
                    }
                }
            )
        else:
            assetsToBurn.append({
                'tokenId': stakeBox["additionalRegisters"]["R5"]["renderedValue"],
                'amount': 1
                })
        if penalty > 0:
            assetsToBurn.append({
                'tokenId': CFG.stakedTokenID,
                'amount': penalty
            })
        if len(assetsToBurn)>0:
            outputs.append({'assetsToBurn': assetsToBurn})

        inBoxesRaw = []
        for box in [stakeStateBox["boxId"],stakeBox["boxId"]]+req.utxos:
            res = requests.get(f'{CFG.ergopadNode}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
            if res.ok:
                inBoxesRaw.append(res.json()['bytes'])
            else:
                return res

        request =  {
                'requests': outputs,
                'fee': int(0.001*nergsPerErg),
                'inputsRaw': inBoxesRaw
            }

        return request



@r.get("/snapshot/", name="staking:snapshot")
def snapshot():
    offset = 0
    limit = 100
    done = False
    addresses = {}
    while not done:
        checkBoxes = getTokenBoxes(tokenId=CFG.stakeTokenID,offset=offset,limit=limit)
        for box in checkBoxes:
            if box["assets"][0]["tokenId"]==CFG.stakeTokenID:
                keyHolder = getNFTBox(box["additionalRegisters"]["R5"]["renderedValue"])
                if keyHolder["address"] not in addresses.keys():
                    addresses[keyHolder["address"]] = 0
                addresses[keyHolder["address"]] += box["assets"][1]["amount"]
        if len(checkBoxes)<limit:
            done=True
        offset += limit
    
    return {
        'stakers': addresses
    }

@r.get("/staked/{address}", name="staking:staked")
def staked(address: str):

    stakeKeys = {}
    res = requests.get(f'{CFG.explorer}/addresses/{address}/balance/confirmed')
    if res.ok:
        for token in res.json()["tokens"]:
            if "Stake Key" in token["name"]:
                stakeKeys[token["tokenId"]] = token
    
    offset = 0
    limit = 100
    done = False
    stakeBoxes = []
    totalStaked = 0
    while not done:
        checkBoxes = getTokenBoxes(tokenId=CFG.stakeTokenID,offset=offset,limit=limit)
        for box in checkBoxes:
            if box["assets"][0]["tokenId"]==CFG.stakeTokenID:
                if box["additionalRegisters"]["R5"]["renderedValue"] in stakeKeys.keys():
                    stakeBoxes.append(box)
                    totalStaked += box["assets"][1]["amount"]
        if len(checkBoxes)<limit:
            done=True
        offset += limit
    
    return {
        'totalStaked': totalStaked,
        'stakeBoxes': stakeBoxes
    }

@r.get("/status/", name="staking:status")
def status():
    stakeStateBox = getNFTBox(CFG.stakeStateNFT)
    stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])

    apy = 29300000.0/stakeStateR4[0]*36500

    return {
        'Total amount staked': stakeStateR4[0]/10**2,
        'Staking boxes': stakeStateR4[2],
        'Cycle start': stakeStateR4[3],
        'APY': apy
    }

@r.get("/compound/", name="staking:compound")
def compound():
    stakeStateBox = getNFTBox(CFG.stakeStateNFT)
    emissionBox = getNFTBox(CFG.emissionNFT)

    stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
    emissionR4 = eval(emissionBox["additionalRegisters"]["R4"]["renderedValue"])

    stakeBoxes = []
    stakeBoxesOutput = []
    offset = 0
    limit = 100
    totalReward = 0

    while len(stakeBoxes) < 100:
        checkBoxes = getTokenBoxes(tokenId=CFG.stakeTokenID,offset=offset,limit=limit)
        for box in checkBoxes:
            if box["assets"][0]["tokenId"]==CFG.stakeTokenID:
                boxR4 = eval(box["additionalRegisters"]["R4"]["renderedValue"])
                if boxR4[0] == emissionR4[1]:
                    stakeBoxes.append(box["boxId"])
                    stakeReward = int(box["assets"][1]["amount"] * emissionR4[3] / emissionR4[0])
                    totalReward += stakeReward
                    stakeBoxesOutput.append({
                        'value': box["value"],
                        'address': box["address"],
                        'assets': [
                            {
                                'tokenId': CFG.stakeTokenID,
                                'amount': 1
                            },
                            {
                                'tokenId': CFG.stakedTokenID,
                                'amount': box["assets"][1]["amount"] + stakeReward
                            }
                        ],
                        'registers': {
                            'R4': encodeLongArray([
                                boxR4[0]+1,
                                boxR4[1]
                            ]),
                            'R5': box["additionalRegisters"]["R5"]["serializedValue"]
                        }
                    })
        if len(checkBoxes)<limit:
            break
    
    stakeStateOutput = {
        'value': stakeStateBox["value"],
        'address': stakeStateBox["address"],
        'assets': stakeStateBox["assets"],
        'registers': {
            'R4': encodeLongArray([
                stakeStateR4[0]+totalReward,
                stakeStateR4[1],
                stakeStateR4[2],
                stakeStateR4[3],
                stakeStateR4[4]
            ])
        }
    }

    emissionAssets = [{
                'tokenId': CFG.emissionNFT,
                'amount': 1
            }]
    if totalReward < emissionBox["assets"][1]["amount"]:
        emissionAssets.append({
            'tokenId': CFG.stakedTokenID,
            'amount': emissionBox["assets"][1]["amount"]-totalReward
        })

    emissionOutput = {
        'value': emissionBox["value"],
        'address': emissionBox["address"],
        'assets': emissionAssets,
        'registers': {
            'R4': encodeLongArray([
                emissionR4[0],
                emissionR4[1],
                emissionR4[2]-len(stakeBoxes),
                emissionR4[3]
            ])
        }
    }

    txFee = max(CFG.txFee,(0.001+0.0005*len(stakeBoxesOutput))*nergsPerErg)

    inBoxesRaw = []
    for box in [stakeStateBox["boxId"],emissionBox["boxId"]]+stakeBoxes+list(getBoxesWithUnspentTokens(nErgAmount=txFee).keys()):
        res = requests.get(f'{CFG.ergopadNode}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
        if res.ok:
            inBoxesRaw.append(res.json()['bytes'])
        else:
            return res

    request =  {
            'requests': [stakeStateOutput,emissionOutput]+stakeBoxesOutput,
            'fee': int(txFee),
            'inputsRaw': inBoxesRaw
        }

    res = requests.post(f'{CFG.ergopadNode}/wallet/transaction/send', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), json=request)   
    logging.debug(res)
    return res.content


@r.get("/emit/", name="staking:emit")
def emit():
    stakeStateBox = getNFTBox(CFG.stakeStateNFT)
    stakePoolBox = getNFTBox(CFG.stakePoolNFT)
    emissionBox = getNFTBox(CFG.emissionNFT)

    stakeStateR4 = eval(stakeStateBox["additionalRegisters"]["R4"]["renderedValue"])
    stakePoolR4 = eval(stakePoolBox["additionalRegisters"]["R4"]["renderedValue"])

    stakeStateOutput = {
        'value': stakeStateBox["value"],
        'address': stakeStateBox["address"],
        'assets': stakeStateBox["assets"],
        'registers': {
            'R4': encodeLongArray([
                stakeStateR4[0],
                stakeStateR4[1]+1,
                stakeStateR4[2],
                stakeStateR4[3]+stakeStateR4[4],
                stakeStateR4[4]
            ])
        }
    }

    newStakePoolAmount = stakePoolBox["assets"][1]["amount"] - stakePoolR4[0]
    if len(emissionBox["assets"]) > 1:
        newStakePoolAmount += emissionBox["assets"][1]["amount"]
    
    stakePoolOutput = {
        'value': stakePoolBox["value"],
        'address': stakePoolBox["address"],
        'registers': {'R4': stakePoolBox["additionalRegisters"]["R4"]["serializedValue"]},
        'assets': [
            {
                'tokenId': stakePoolBox["assets"][0]["tokenId"],
                'amount': stakePoolBox["assets"][0]["amount"]
            },
            {
                'tokenId': stakePoolBox["assets"][1]["tokenId"],
                'amount': newStakePoolAmount
            }
        ]
    }

    emissionOutput = {
        'value': emissionBox["value"],
        'address': emissionBox["address"],
        'assets': [
            {
                'tokenId': emissionBox["assets"][0]["tokenId"],
                'amount': emissionBox["assets"][0]["amount"]
            },
            {
                'tokenId': stakePoolBox["assets"][1]["tokenId"],
                'amount': stakePoolR4[0]
            }
        ],
        'registers': {
            'R4': encodeLongArray([
                stakeStateR4[0],
                stakeStateR4[1],
                stakeStateR4[2],
                stakePoolR4[0]
            ])
        }
    }

    inBoxesRaw = []
    for box in [stakeStateBox["boxId"],stakePoolBox["boxId"],emissionBox["boxId"]]+list(getBoxesWithUnspentTokens(nErgAmount=CFG.txFee).keys()):
        res = requests.get(f'{CFG.ergopadNode}/utxo/withPool/byIdBinary/{box}', headers=dict(headers), timeout=2)
        if res.ok:
            inBoxesRaw.append(res.json()['bytes'])
        else:
            return res

    request =  {
            'requests': [stakeStateOutput,stakePoolOutput,emissionOutput],
            'fee': int(0.001*nergsPerErg),
            'inputsRaw': inBoxesRaw
        }

    res = requests.post(f'{CFG.ergopadNode}/wallet/transaction/send', headers=dict(headers, **{'api_key': CFG.ergopadApiKey}), json=request)   
    logging.debug(res)
    return res.content



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

    