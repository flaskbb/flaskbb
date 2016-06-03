from __future__ import unicode_literals

import requests
import json

CABINET = 'http://127.0.0.1:8000/cabinet/auth'
CABINET_AUTH = CABINET + '/login/'
CABINET_REGISTER = CABINET + '/create/'

# r = requests.post(CABINET_AUTH, json={"login": "dante1", "password": "12345"})
# print(json.loads(r.text))


def create_cabinet_user(username, password, email):
    req = requests.post(CABINET_REGISTER, json={"login": username, "password": password, 'email': email})
    if not req.text:
        return False

    res = json.loads(req.text)
    status = res.get('status')
    if status != 'OK':
        # return res.get('message', '')
        return False

    return True
