import hashlib
import hmac
import json
import random
import uuid

import requests as rq
from decouple import config


MAIN_SERVICE_URL = config('MAIN_SERVICE_URL', 'http://127.0.1.1:8000')
SHARED_SECRET_KEY_SERVICE = config('SHARED_SECRET_KEY_SERVICE', 'secret-key').encode()


def add_headers(payload=None):
    headers = {
        'Content-Type': 'application/json',
    }

    if payload:
        payload_json = json.dumps(payload)

        payload_json = payload_json.encode()
        print(payload_json)
        hash_data = hmac.new(SHARED_SECRET_KEY_SERVICE, payload_json, hashlib.sha256)
        x_hmac_signature = hash_data.hexdigest()
        headers['X-HMAC-SIGNATURE-SERVICE'] = x_hmac_signature

    return headers


def get_user_info():
    url = f'{MAIN_SERVICE_URL}user/get_users_list/'

    payload = {
        "random_num": uuid.uuid4().hex
    }
    headers = add_headers(payload=payload)
    print(payload, headers)

    response = rq.request(
        'POST',
        url,
        headers=headers,
        json=payload
    )

    return response


def get_user_balance_info(payload: dict):
    url = f'{MAIN_SERVICE_URL}user/get_user_balance/'

    headers = add_headers(payload=payload)
    response = rq.request(
        'POST',
        url,
        headers=headers,
        json=payload
    )

    return response
