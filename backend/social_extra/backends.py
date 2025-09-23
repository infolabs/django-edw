# -*- coding: utf-8 -*-
import os
import tempfile
import base64
import datetime
from urllib.parse import urlencode, unquote

import pytz
import uuid
import jwt
import re
import hmac
import time
import hashlib
import requests
from requests.exceptions import RequestException
import six

from django import VERSION
from django.http import HttpResponseRedirect
from django.conf import settings

from social_core.backends.oauth import BaseOAuth2
from social_core.backends.vk import VKOAuth2
from social_core.backends.telegram import TelegramAuth as TelegramAuthBase
from social_core.exceptions import AuthFailed, AuthMissingParameter

from edw.utils.hash_helpers import create_hash

from social_core.utils import handle_http_errors

import logging
auth_logger = logging.getLogger('logauth')


URL_ERROR_PATTERN = '/cabinet/error/?code={}&ajax=1'


class ERROR_CODES:
    ESIA_AUTH = 3

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
        try:
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
        except RequestException:
            return ERROR_CODES.ESIA_AUTH
        else:
            return response.content
    elif backend == 'cryptopro':
        import pycades
        container_pin = getattr(
            settings,
            'SOCIAL_AUTH_ESIA_CRYPTO_KEY_CONTAINER_PIN',
            '',
        )
        store = pycades.Store()
        store.Open(
            pycades.CAPICOM_CURRENT_USER_STORE,
            pycades.CAPICOM_MY_STORE,
            pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED,
        )
        certs = store.Certificates
        certs_count = certs.Count
        if certs_count < 1:
            raise Exception('Cryptopro has no installed certificates to sign data.')
        signer = pycades.Signer()
        signer.Certificate = certs.Item(1)
        signer.CheckCertificate = True
        if container_pin:
            signer.KeyPin = container_pin
        signedData = pycades.SignedData()
        signedData.Content = data
        signature = signedData.SignCades(signer, pycades.CADESCOM_CADES_BES)
        return signature.encode('utf-8')
    else:
        raise Exception('Unknown cryptography backend. Use openssl or m2crypto value.')


def sign_params(params, certificate_file, private_key_file, backend='m2crypto'):
    plaintext = ''.join([params.get('scope', ''), params.get('timestamp', ''),
                        params.get('client_id', ''), params.get('state', '')])

    raw_client_secret = smime_sign(certificate_file, private_key_file, plaintext, backend)

    if raw_client_secret == ERROR_CODES.ESIA_AUTH:
        params.update(crypto_error=True)
    else:
        client_secret = base64.urlsafe_b64encode(raw_client_secret)
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
    GET_ALL_EXTRA_DATA = True

    MAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')

    def state_token(self):
        return str(uuid.uuid4())

    def auth_url(self):
        """Return redirect url"""
        state = self.get_or_create_state()
        params = self.auth_params(state)

        if params.get('crypto_error'):
            return URL_ERROR_PATTERN.format(ERROR_CODES.ESIA_AUTH)

        params.update(self.get_scope_argument())
        params.update(self.auth_extra_arguments())
        params = urlencode(params)
        if not self.REDIRECT_STATE:
            # redirect_uri matching is strictly enforced, so match the
            # providers value exactly.
            params = unquote(params)
        return f"{self.authorization_url()}?{params}"

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
            'patronymic': 'middleName',
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

        response['mobile'] = response['mobile'].get('value', '')
        response['email'] = response['email'].get('value', '')
        # У поля username ограничение 30 символов
        response['username'] = create_hash(response['email'])[:30]
        response['fullname'] = " ".join(filter(
            None, [response['first_name'], response['patronymic'], response['last_name']])
        )

        fields = ['is_trusted', 'username', 'fullname', 'organisations']
        for k in ['info', 'contacts']:
            fields.extend(self.DETAILS_MAP[k].keys())

        return {k: v for k, v in list(response.items()) if k in fields}

    def user_data(self, access_token, *args, **kwargs):

        id_token = kwargs['response']['id_token']
        payload = (jwt.decode(id_token, verify=False) if VERSION[0] < 2 else
                   jwt.decode(id_token, algorithms=['HS256'], options={'verify_signature':False}))

        oid = payload.get('urn:esia:sbj', {}).get('urn:esia:sbj:oid')
        is_trusted = payload.get('urn:esia:sbj', {}).get('urn:esia:sbj:is_tru')
        ret = {'id': oid, 'is_trusted': bool(is_trusted)}
        headers = {'Authorization': "Bearer %s" % access_token}

        base_url = '{base}{info}/{oid}'.format(base=self.BASE_URL, info=self.USER_INFO_PATH, oid=oid)

        try:
            info = self.get_json(base_url, headers=headers)
            contacts = self.get_json(base_url + '/ctts?embed=(elements)', headers=headers)
            elements = contacts['elements']

            if 'contacts' in self.get_scope():
                addresses = self.get_json(base_url + '/addrs?embed=(elements)', headers=headers)
                elements.extend(addresses['elements'])
            if 'usr_org' in self.get_scope():
                orgs = self.get_json(base_url + '/roles', headers=headers)
                if orgs and orgs.get('elements') and len(orgs.get('elements')) > 0:
                    ret['organisations'] = orgs.get('elements')
        except RequestException:
            return HttpResponseRedirect(URL_ERROR_PATTERN.format(ERROR_CODES.ESIA_AUTH))

        for k, v in self.DETAILS_MAP['info'].items():
            ret[k] = info.get(v, '')

        for k, v in self.DETAILS_MAP['contacts'].items():
            if k not in list(ret.keys()):
                ret[k] = {}
            for e in elements:
                if e['type'] == v:
                    ret[k] = e

        return ret

class EsiaOAuth2Test(EsiaOAuth2):
    """
    Бэкенд для тестирования ЕСИА
    Эмулирует ответы от ЕСИА
    """
    name = 'esia'

    BASE_URL = '/oauth/complete/esia/'
    CERTIFICATE = ''
    PRIVKEY = ''

    AUTHORIZATION_PATH = ''
    TOKEN_EXCHANGE_PATH = ''
    USER_INFO_PATH = ''

    ACCESS_TOKEN_METHOD = 'POST'
    AUTHORIZATION_URL = BASE_URL + AUTHORIZATION_PATH
    ACCESS_TOKEN_URL = BASE_URL + TOKEN_EXCHANGE_PATH
    DEFAULT_SCOPE = ['openid', 'email', 'fullname', 'mobile']
    EXTRA_DATA = [('id', 'id')]
    GET_ALL_EXTRA_DATA = True

    MAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')

    def state_token(self):
        return str(uuid.uuid4())

    def add_and_sign_params(self, params):
        # # Test signing
        # crypto_backend = self.setting('CRYPTO', 'm2crypto')
        # sign_params(
            # params,
            # certificate_file=None,
            # private_key_file=None,
            # backend=crypto_backend
        # )
        return params

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        access_token = 'eyJ2ZXIiOjEsInR5cCI6IkpXVCIsInNidCI6ImFjY2VzcyIsImFsZyI6IlJTMjU2In0.eyJuYmYiOjE2NDkxNjIxMjYsInNjb3BlIjoiZW1haWw_b2lkPTEwMTk3OTczOTEgaW5uP29pZD0xMDE5Nzk3MzkxIG9wZW5pZCBtb2JpbGU_b2lkPTEwMTk3OTczOTEgYmlydGhkYXRlP29pZD0xMDE5Nzk3MzkxIGZ1bGxuYW1lP29pZD0xMDE5Nzk3MzkxIGdlbmRlcj9vaWQ9MTAxOTc5NzM5MSB1c3Jfb3JnP29pZD0xMDE5Nzk3MzkxIGNvbnRhY3RzP29pZD0xMDE5Nzk3MzkxIiwiaXNzIjoiaHR0cDpcL1wvZXNpYS5nb3N1c2x1Z2kucnVcLyIsInVybjplc2lhOnNpZCI6ImZkMGI1MzMzLWNjZWItNDNlMy1iNTY3LTc3ZTI5OTVjZTJmNiIsInVybjplc2lhOnNial9pZCI6MTAxOTc5NzM5MSwiZXhwIjoxNjQ5MTY1NzI2LCJpYXQiOjE2NDkxNjIxMjYsImNsaWVudF9pZCI6IjE1OTIwNCJ9.MEvKb7j2IuUD7ZOuKrAB3qObXdwigGMUZMXnyCzq-SgvlBZF-yR-fhm2L0Iyj59QAHTr_vCyWpKGZoi6V_jLCVJFwGFeKkJI-p6_TCoHmoRG2iLA5VOsZqc4s3Ov0pQaLYy95JmsrT92QfRJsmkE3DOJuS0o77QRKfoY0l2N9pWSUIGyeJ73qJMk5jQvz-jPQlRFGPnCgbHZFIugXvuJa86soHWAvYmpdc4IaRcXCYlXwps6HVLaX8X5QvbFlGIQCnxpWHCz1PkzsDwvzVkN1c2KOgItSGYk8rk9xQmKXGWCvHkZSnH9r9G_-EuXrfH2-_S3N8mP4QEDGIMOiyswrw'
        return self.do_auth(access_token, *args, **kwargs)

    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        data = self.user_data(access_token, *args, **kwargs)
        response = kwargs.get('response') or {}
        response.update(data or {})
        if 'access_token' not in response:
            response['access_token'] = access_token
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def request_access_token(self, *args, **kwargs):
        return {'response':
                    {'access_token': 'eyJ2ZXIiOjEsInR5cCI6IkpXVCIsInNidCI6ImFjY2VzcyIsImFsZyI6IlJTMjU2In0.eyJuYmYiOjE2NDkxNjIxMjYsInNjb3BlIjoiZW1haWw_b2lkPTEwMTk3OTczOTEgaW5uP29pZD0xMDE5Nzk3MzkxIG9wZW5pZCBtb2JpbGU_b2lkPTEwMTk3OTczOTEgYmlydGhkYXRlP29pZD0xMDE5Nzk3MzkxIGZ1bGxuYW1lP29pZD0xMDE5Nzk3MzkxIGdlbmRlcj9vaWQ9MTAxOTc5NzM5MSB1c3Jfb3JnP29pZD0xMDE5Nzk3MzkxIGNvbnRhY3RzP29pZD0xMDE5Nzk3MzkxIiwiaXNzIjoiaHR0cDpcL1wvZXNpYS5nb3N1c2x1Z2kucnVcLyIsInVybjplc2lhOnNpZCI6ImZkMGI1MzMzLWNjZWItNDNlMy1iNTY3LTc3ZTI5OTVjZTJmNiIsInVybjplc2lhOnNial9pZCI6MTAxOTc5NzM5MSwiZXhwIjoxNjQ5MTY1NzI2LCJpYXQiOjE2NDkxNjIxMjYsImNsaWVudF9pZCI6IjE1OTIwNCJ9.MEvKb7j2IuUD7ZOuKrAB3qObXdwigGMUZMXnyCzq-SgvlBZF-yR-fhm2L0Iyj59QAHTr_vCyWpKGZoi6V_jLCVJFwGFeKkJI-p6_TCoHmoRG2iLA5VOsZqc4s3Ov0pQaLYy95JmsrT92QfRJsmkE3DOJuS0o77QRKfoY0l2N9pWSUIGyeJ73qJMk5jQvz-jPQlRFGPnCgbHZFIugXvuJa86soHWAvYmpdc4IaRcXCYlXwps6HVLaX8X5QvbFlGIQCnxpWHCz1PkzsDwvzVkN1c2KOgItSGYk8rk9xQmKXGWCvHkZSnH9r9G_-EuXrfH2-_S3N8mP4QEDGIMOiyswrw',
                     'refresh_token': 'bb809750-71bc-2406-88d1-2388a4be5187',
                     'id_token': 'eyJ2ZXIiOjAsInR5cCI6IkpXVCIsInNidCI6ImlkIiwiYWxnIjoiUlMyNTYifQ.eyJhdWQiOiIxNTkyMDQiLCJzdWIiOjEwMTk3OTczOTEsIm5iZiI6MTY0OTE2MjEyNiwiYW1yIjoiUFdEIiwidXJuOmVzaWE6YW1kIjoiUFdEIiwiYXV0aF90aW1lIjoxNjQ5MTYyMTI2LCJpc3MiOiJodHRwOlwvXC9lc2lhLmdvc3VzbHVnaS5ydVwvIiwidXJuOmVzaWE6c2lkIjoiZmQwYjUzMzMtY2NlYi00M2UzLWI1NjctNzdlMjk5NWNlMmY2IiwidXJuOmVzaWE6c2JqIjp7InVybjplc2lhOnNiajp0eXAiOiJQIiwidXJuOmVzaWE6c2JqOmlzX3RydSI6dHJ1ZSwidXJuOmVzaWE6c2JqOm9pZCI6MTAxOTc5NzM5MSwidXJuOmVzaWE6c2JqOm5hbSI6Ik9JRC4xMDE5Nzk3MzkxIn0sImV4cCI6MTY0OTE3MjkyNiwiaWF0IjoxNjQ5MTYyMTI2fQ.Q4Mt5gmsqZqcUXbhbBzAgeSGShhKOA856vx6lCkdWOBMWuFNGQvuDixsJVolSlsuwJJqA8Zh7LQcByHHqyqNc1ed2J51nKulrm7hgmDSst50WuASld2A99bE5_Jn6GNlCsnu3xi3KgVtM3lZYhJEJkxPGQ9wyLmMQUXQrNvy_w2nPS6ZGsZr_dgT5_0SLNf4hweDEPxcj8l-EEnHYNU79j4srV8hKMsmPj0gewNUS_P9N2cTO0Mzw0Ihg9j5kfPZuLAejp0ZwE6dlhtKoBkltTwwWhQTYBXSjhLYAj5lzz7dd8dn8eIK86qWhxzY5rtVYAyWaGPKA-MY24VLEq5lHQ',
                     'state': '7497a6ec-6085-4722-9b35-367ab2139b6a',
                     'token_type': 'Bearer',
                     'expires_in': 3600},
                'user': None, 'request': ''
                }

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

    def get_user_details(self, response):
        response['mobile'] = response['mobile'].get('value', '')
        response['email'] = response['email'].get('value', '')
        # У поля username ограничение 30 символов
        response['username'] = create_hash(response['email'])[:30]
        response['fullname'] = " ".join(filter(
            None, [response['first_name'], response['patronymic'], response['last_name']])
        )

        fields = ['is_trusted', 'username', 'fullname', 'organisations']
        for k in ['info', 'contacts']:
            fields.extend(self.DETAILS_MAP[k].keys())

        return {k: v for k, v in list(response.items()) if k in fields}

    def user_data(self, access_token, *args, **kwargs):
        payload = {'aud': '159204',
                   'sub': 1019777777,
                   'nbf': 1649162126,
                   'amr': 'PWD', 'urn:esia:amd': 'PWD',
                   'auth_time': 1649162126,
                   'iss': 'http://esia.gosuslugi.ru/',
                   'urn:esia:sid': 'fd0b5333-cceb-43e3-b567-77e2995ce2f6',
                   'urn:esia:sbj': {'urn:esia:sbj:typ': 'P',
                                    'urn:esia:sbj:is_tru': True,
                                    'urn:esia:sbj:oid': 1019777777,
                                    'urn:esia:sbj:nam': 'OID.1019777777'
                                    },
                   'exp': 1649172926,
                   'iat': 1649162126
                   }

        oid = payload.get('urn:esia:sbj', {}).get('urn:esia:sbj:oid')
        is_trusted = payload.get('urn:esia:sbj', {}).get('urn:esia:sbj:is_tru')
        ret = {'id': oid, 'is_trusted': bool(is_trusted)}
        info = {'stateFacts': ['EntityRoot'],
                'firstName': 'Иван',
                'lastName': 'Иванов-Тест',
                'middleName': 'Иванович',
                'birthDate': '01.10.1981',
                'gender': 'M',
                'trusted': True,
                'inn': '312320000000',
                'updatedOn': 1519766386,
                'status': 'REGISTERED',
                'verifying': False,
                'rIdDoc': 23560000,
                'containsUpCfmCode': False,
                'eTag': 'BBBB5286519A9A0553BC60BE4EAAF4C646FFFFFF'}

        contacts = {'stateFacts': ['hasSize'],
                    'size': 2,
                    'eTag': 'DDDDDDD0A111E97A0DB0E308421F4BB6DA6CCCCC',
                    'elements': [
                        {'stateFacts': ['Identifiable'],
                         'id': 66333306,
                         'type': 'EML',
                         'vrfStu': 'VERIFIED',
                         'value': 'esiatest@excentrics.ru',
                         'eTag': '8AF8A61E9950D736BC98D2728991F20BF88FFFFF'
                         },
                        {'stateFacts': ['Identifiable'],
                         'id': 66333305,
                         'type': 'MBT',
                         'vrfStu': 'VERIFIED',
                         'value': '+7(910)2206415',
                         'eTag': '70AA666B843F225E247AEB143B3985E9BFDDDDDD'
                         }]
                    }

        elements = contacts['elements']

        addresses = {'stateFacts': ['hasSize'],
                     'size': 2,
                     'eTag': '13FFFFF71D9D7E40D0DB31A6A032546B46222222',
                     'elements': [
                         {'stateFacts': ['Identifiable'],
                          'id': 29333307,
                          'type': 'PRG',
                          'addressStr': 'обл Белгородская, г Белгород, пр-кт Ватутина',
                          'fiasCode': 'b18a3ed8-4339-44fb-bf8a-03d5e07e40c4',
                          'flat': '99',
                          'countryId': 'RUS',
                          'house': '9',
                          'zipCode': '308024',
                          'city': 'Белгород',
                          'street': 'Ватутина',
                          'region': 'Белгородская',
                          'vrfDdt': '0,0,0',
                          'eTag': 'E26EEEEEB0DA5F421AD5F191D605DE20F395FBF2'
                          },
                         {'stateFacts': ['Identifiable'],
                          'id': 24333385,
                          'type': 'PLV',
                          'addressStr': 'Белгородская обл, г Белгород, ул Садовая',
                          'fiasCode': 'f400cf4b-8888-4f8f-896b-bb580f1cf6aa',
                          'flat': '1',
                          'countryId': 'RUS',
                          'house': '5',
                          'zipCode': '308000',
                          'city': 'г Белгород',
                          'street': 'ул Мира',
                          'region': 'Белгородская обл',
                          'vrfDdt': '0,0,0',
                          'fiasCode2': '31-0-000-001-000-000-0318-0000-000',
                          'eTag': '0EEEEEE11948665712E7E37877BF49AFDB6A1A72'
                          }]
                     }
        elements.extend(addresses['elements'])
        orgs = {'stateFacts': ['hasSize'],
                'size': 1,
                'elements': [
                    {'oid': 1063633333,
                     'prnOid': 1019777777,
                     'fullName': 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КОМПАНИЯ"',
                     'shortName': 'ООО "КОМПАНИЯ"',
                     'ogrn': '1163123077777',
                     'type': 'LEGAL',
                     'chief': True,
                     'admin': False,
                     'phone': '+7(4722)333333',
                     'email': 'team@infolabs.ru',
                     'active': True,
                     'hasRightOfSubstitution': True,
                     'hasApprovalTabAccess': False,
                     'isLiquidated': False}]
                }
        if orgs and orgs.get('elements') and len(orgs.get('elements')) > 0:
            ret['organisations'] = orgs.get('elements')

        for k, v in self.DETAILS_MAP['info'].items():
            ret[k] = info.get(v, '')

        for k, v in self.DETAILS_MAP['contacts'].items():
            if k not in list(ret.keys()):
                ret[k] = {}
            for e in elements:
                if e['type'] == v:
                    ret[k] = e

        return ret


class VKOAuth2Https(VKOAuth2):
    AUTHORIZATION_URL = 'https://oauth.vk.ru/authorize'


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
