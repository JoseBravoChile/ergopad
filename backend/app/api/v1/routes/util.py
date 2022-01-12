# import requests
import ssl
import pandas as pd

from sqlalchemy import create_engine
from fastapi import APIRouter, Response, status #, Request
from fastapi.encoders import jsonable_encoder
from typing import Optional
from pydantic import BaseModel
from time import time
from smtplib import SMTP
from config import Config, Network # api specific config
CFG = Config[Network]

util_router = r = APIRouter()

#region BLOCKHEADER
"""
Utilities
---------
Created: vikingphoenixconsulting@gmail.com
On: 20211129
Purpose: Common support requests

Notes: 
"""
#endregion BLOCKHEADER

#region INIT
DEBUG = CFG.debug
st = time() # stopwatch

class Email(BaseModel):
    to: str
    # sender: str
    subject: Optional[str] = 'ErgoPad'
    body: Optional[str] = ''

    class Config:
        schema_extra = {
            'to': 'hello@world.com',
            'subject': 'greetings',
            'body': 'this is a message.'
        }
#endregion INIT

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

@r.post("/email")
async def email(email: Email):
    usr = CFG.emailUsername
    pwd = CFG.emailPassword
    svr = CFG.emailSMTP
    frm = CFG.emailFrom
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)

    # create connection
    logging.info(f'creating connection for: {svr} as {usr}')
    con = SMTP(svr, 587)
    res = con.ehlo()
    res = con.starttls(context=ctx)
    if res[0] == 220: logging.info('starttls success')
    else: logging.error(res)
    res = con.ehlo()
    res = con.login(usr, pwd)
    if res[0] == 235: logging.info('login success')
    else: logging.error(res)

    msg = f"""From: {frm}\nTo: {email.to}\nSubject: {email.subject}\n\n{email.body}"""
    res = con.sendmail(frm, email.to, msg) # con.sendmail(frm, 'erickson.winter@gmail.com', msg)
    if res == {}: logging.info('message sent')
    else: logging.error(res)

    return {'status': 'success', 'detail': f'email sent to {email.to}'}

