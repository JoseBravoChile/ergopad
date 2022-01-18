import logging
import requests

from starlette.responses import JSONResponse
from fastapi import APIRouter, status
from config import Config, Network  # api specific config

assembler_router = r = APIRouter()

DEBUG = True
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(
    format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

CFG = Config[Network]
headers = {'Content-Type': 'application/json'}


@r.get("/return/{wallet}/{smartContract}", name="assembler:return")
async def assemblerReturn(wallet: str, smartContract: str):
    try:
        res = requests.get(f'{CFG.assembler}/return/{wallet}/{smartContract}')
        return JSONResponse(status_code=res.status_code, content=res.json())
    except:
        logging.debug(
            f'request failed for "wallet": {wallet}, "smartContract": {smartContract}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'network failure could not connect to assembler')


@r.get("/status/{assemblerId}")
async def assemblerStatus(assemblerId: str):
    try:
        res = requests.get(f'{CFG.assembler}/result/{assemblerId}')
        return JSONResponse(status_code=res.status_code, content=res.json())
    except:
        logging.debug(f'request failed for "assemblerId": {assemblerId}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'network failure could not connect to assembler')
