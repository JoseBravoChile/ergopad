from requests import get
from time import sleep

tot = 0
while True: 
    res = get('https://ergopad.io/api/vesting/redeem/Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp', verify=False); 
    if res.ok:
        tot += res.json()['amount']
    
    print(f'{tot} boxes; sleeping...'); 
    sleep(200)