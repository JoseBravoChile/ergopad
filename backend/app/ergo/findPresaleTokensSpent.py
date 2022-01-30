import requests

headers = {'Content-Type': 'application/json', 'api_key': 'M7&5bEXE6F46Fjyo'}
res = requests.get('http://ergonode:9053/wallet/transactions', headers=headers)

tot = 0
if res.ok:
    tx = res.json()
    for t in tx:
        # print(f"tx: {t['id']}")
        for o in t['outputs']:
            if 'assets' in o and 'additionalRegisters' in o:
                if o['address'] != '9gibNzudNny7MtB725qGM3Pqftho1SMpQJ2GYLYRDDAftMaC285' and 'R5' in o['additionalRegisters']:
                    if o['additionalRegisters']['R5'] == '0580e4a0ca13':
                        for a in o['assets']:
                            if 'tokenId' in a:
                                if a['tokenId'] == 'd71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413':
                                    tot += a['amount']

    print(f'Total ErgoPad tokens: {tot/100:,.0f}')
else:
    print(f'ERR: {res.content}')

