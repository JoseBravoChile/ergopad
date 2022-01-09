from ergo.updateAllowance import handleAllowance
from time import sleep

import asyncio

while True:
    asyncio.run(handleAllowance())
    sleep(10)
