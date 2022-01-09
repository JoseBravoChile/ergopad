import requests


def ping(host, port, path):
    try:
        res = requests.get(f'http://{host}:{port}/{path}')
        if res.status_code == 200:
            return {'status': 'ok', 'body': res.json()}

    except Exception as e:
        return {'status': 'error', 'detail': e}


if __name__ == '__main__':
    res = ping('127.0.0.1', 8000, 'api/ping')
    print(res)
    assert(res['status'] == 'ok')
