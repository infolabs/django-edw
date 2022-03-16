# -*- coding: utf-8 -*-
import os
import tempfile
import base64
import datetime
import pytz
import uuid
import jwt
import re
import hmac
import time
import hashlib
import requests

from django.conf import settings
from django.utils import six

from social_core.backends.oauth import BaseOAuth2
from social_core.backends.vk import VKOAuth2
from social_core.backends.telegram import TelegramAuth as TelegramAuthBase
from social_core.exceptions import AuthFailed, AuthMissingParameter

from edw.utils.hash_helpers import create_hash

import logging
auth_logger = logging.getLogger('logauth')

# https://github.com/sokolovs/esia-oauth2/blob/master/esia/utils.py

def get_timestamp():
    return datetime.datetime.now(pytz.utc).strftime('%Y.%m.%d %H:%M:%S %z').strip()


def smime_sign(certificate_file, private_key_file, data, backend='m2crypto'):

    if backend == 'm2crypto' or backend is None:
        from M2Crypto import SMIME, BIO

        if not isinstance(data, bytes):
            data = bytes(str(data), encoding='utf8')

        signer = SMIME.SMIME()
        signer.load_key(private_key_file, certificate_file)
        p7 = signer.sign(BIO.MemoryBuffer(data), flags=SMIME.PKCS7_DETACHED, algo='sha256')
        signed_message = BIO.MemoryBuffer()
        p7.write_der(signed_message)
        return signed_message.read()

    elif backend == 'openssl':
        source_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        source_file.write(data)
        source_file.close()
        source_path = source_file.name

        destination_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        destination_file.close()
        destination_path = destination_file.name

        cmd = 'openssl smime -sign -md sha256 -in {f_in} -signer {cert} -inkey {key} -out {f_out} -outform DER'
        os.system(cmd.format(
            f_in=source_path,
            cert=certificate_file,
            key=private_key_file,
            f_out=destination_path,
        ))

        signed_message = open(destination_path, 'rb').read()
        os.unlink(source_path)
        os.unlink(destination_path)
        return signed_message

    elif backend == 'openssl-gost':
        source_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        source_file.write(data)
        source_path = source_file.name
        source_file.close()

        destination_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        destination_path = destination_file.name
        destination_file.close()

        # openssl compiled with gost 2012 support
        cmd = ('LD_LIBRARY_PATH=/usr/local/ssl/lib/'
               ' /usr/local/ssl/bin/openssl smime -sign -md sha256 -signer {cert}'
               ' -engine gost -in {f_in} -out {f_out} -outform DER')

        os.system(cmd.format(
            f_in=source_path,
            cert=certificate_file,
            f_out=destination_path,
        ))

        with open(destination_path, 'rb') as content_file:
            signed_message = content_file.read()
        os.unlink(source_path)
        os.unlink(destination_path)
        return signed_message
    elif backend == 'crypto-service':
        service_url = settings.SOCIAL_AUTH_ESIA_CRYPTO_SERVICE_URL
        service_token = settings.SOCIAL_AUTH_ESIA_CRYPTO_SERVICE_TOKEN
        response = requests.post(
            url=service_url,
            headers={
                'Authorization':  'Bearer ' + service_token,
                'Content-Type': 'application/octet-stream',
                'Accept': 'application/pkcs7-signature',
                'Content-Encoding': 'binary',
                'Accept-Encoding': 'binary',
            },
            data=data
        )
        response.raise_for_status()
        return response.content
    else:
        raise Exception('Unknown cryptography backend. Use openssl or m2crypto value.')


def sign_params(params, certificate_file, private_key_file, backend='m2crypto'):
    plaintext = ''.join([params.get('scope', ''), params.get('timestamp', ''),
                        params.get('client_id', ''), params.get('state', '')])
    raw_client_secret = smime_sign(certificate_file, private_key_file, plaintext, backend)
    client_secret = base64.urlsafe_b64encode(raw_client_secret)
    if six.PY2:
        client_secret = client_secret.decode('utf-8')
    params.update(
        client_secret=client_secret,
    )
    return params


class EsiaOAuth2(BaseOAuth2):
    name = 'esia'

    BASE_URL = settings.SOCIAL_AUTH_ESIA_URL
    CERTIFICATE = settings.SOCIAL_AUTH_ESIA_CERTIFICATE
    PRIVKEY = settings.SOCIAL_AUTH_ESIA_PRIVKEY

    AUTHORIZATION_PATH = '/aas/oauth2/ac'
    TOKEN_EXCHANGE_PATH = '/aas/oauth2/te'
    USER_INFO_PATH = '/rs/prns'

    ACCESS_TOKEN_METHOD = 'POST'
    AUTHORIZATION_URL = BASE_URL + AUTHORIZATION_PATH
    ACCESS_TOKEN_URL = BASE_URL + TOKEN_EXCHANGE_PATH
    DEFAULT_SCOPE = ['openid', 'email', 'fullname', 'mobile']
    EXTRA_DATA = [('id', 'id')]

    MAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')

    def state_token(self):
        return str(uuid.uuid4())

    def add_and_sign_params(self, params):
        params['timestamp'] = get_timestamp()
        params.update(self.get_scope_argument())
        certificate_file = self.CERTIFICATE
        private_key_file = self.PRIVKEY
        crypto_backend = self.setting('CRYPTO', 'm2crypto')
        return sign_params(
            params,
            certificate_file=certificate_file,
            private_key_file=private_key_file,
            backend=crypto_backend
        )

    def auth_params(self, state=None):
        params = super(EsiaOAuth2, self).auth_params(state)
        params['response_type'] = 'code'
        params['access_type'] = 'offline'
        return self.add_and_sign_params(params)

    def auth_complete_params(self, state=None):
        params = super(EsiaOAuth2, self).auth_complete_params(state)
        params['token_type'] = 'Bearer'
        params['state'] = state
        return self.add_and_sign_params(params)

    DETAILS_MAP = {
        'info': {
            'first_name': 'firstName',
            'middle_name': 'middleName',
            'last_name': 'lastName',
            'birth_date': 'birthDate',
            'gender': 'gender',
        },
        'contacts': {
            'email': 'EML',
            'mobile': 'MBT',
            'reg_addr': 'PRG',
            'liv_addr': 'PLV',
        }
    }

    def get_user_details(self, response):
        auth_logger.debug("EsiaOAuth2 get_user_details +++++++")
        auth_logger.debug(response)
        response['mobile'] = response['mobile'].get('value', '')
        response['email'] = response['email'].get('value', '')
        # У поля username ограничение 30 символов
        response['username'] = create_hash(response['email'])[:30]
        response['fullname'] = " ".join(filter(
            None, [response['first_name'], response['middle_name'], response['last_name']])
        )

        fields = ['is_trusted', 'username', 'fullname']
        for k in ['info', 'contacts']:
            fields.extend(self.DETAILS_MAP[k].keys())
        return {k: v for k, v in list(response.items()) if k in fields}

    def user_data(self, access_token, *args, **kwargs):
        auth_logger.debug("EsiaOAuth2 user_data +++++++")
        auth_logger.debug(kwargs)

        id_token = kwargs['response']['id_token']
        payload = jwt.decode(id_token, verify=False)

        oid = payload.get('urn:esia:sbj', {}).get('urn:esia:sbj:oid')
        is_trusted = payload.get('urn:esia:sbj', {}).get('urn:esia:sbj:is_tru')
        headers = {'Authorization': "Bearer %s" % access_token}

        base_url = '{base}{info}/{oid}'.format(base=self.BASE_URL, info=self.USER_INFO_PATH, oid=oid)
        info = self.get_json(base_url, headers=headers)
        contacts = self.get_json(base_url + '/ctts?embed=(elements)', headers=headers)
        elements = contacts['elements']

        if 'contacts' in self.get_scope():
            addresses = self.get_json(base_url + '/addrs?embed=(elements)', headers=headers)
            elements.extend(addresses['elements'])

        ret = {'id': oid, 'is_trusted': bool(is_trusted)}

        for k, v in self.DETAILS_MAP['info'].items():
            ret[k] = info.get(v, '')

        for k, v in self.DETAILS_MAP['contacts'].items():
            if k not in list(ret.keys()):
                ret[k] = {}
            for e in elements:
                if e['type'] == v:
                    ret[k] = e

        auth_logger.debug("EsiaOAuth2 user_data res:")
        auth_logger.debug(ret)
        return ret


class VKOAuth2Https(VKOAuth2):
    AUTHORIZATION_URL = 'https://oauth.vk.com/authorize'


class TelegramAuth(TelegramAuthBase):
    def verify_data(self, response):
        bot_token = self.setting('BOT_TOKEN')
        if bot_token is None:
            raise AuthMissingParameter('telegram',
                                       'SOCIAL_AUTH_TELEGRAM_BOT_TOKEN')

        received_hash_string = response.get('hash')
        auth_date = response.get('auth_date')

        if received_hash_string is None or auth_date is None:
            raise AuthMissingParameter('telegram', 'hash or auth_date')

        data_check_string = ['{}={}'.format(k, v)
                             for k, v in response.items() if k != 'hash' and k != 'next']
        data_check_string = '\n'.join(sorted(data_check_string))
        secret_key = hashlib.sha256(str(bot_token).encode('utf-8')).digest()
        built_hash = hmac.new(secret_key,
                              msg=str(data_check_string).encode('utf-8'),
                              digestmod=hashlib.sha256).hexdigest()
        current_timestamp = int(time.time())
        auth_timestamp = int(auth_date)
        if current_timestamp - auth_timestamp > 86400:
            raise AuthFailed('telegram', 'Auth date is outdated')
        if built_hash != received_hash_string:
            raise AuthFailed('telegram', 'Invalid hash supplied')
