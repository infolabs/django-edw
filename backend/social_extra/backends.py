# -*- coding: utf-8 -*-
import os
import tempfile
import base64
import datetime
import pytz
import uuid
import jwt
import re

from django.conf import settings
from social_core.backends.oauth import BaseOAuth2


# https://github.com/sokolovs/esia-oauth2/blob/master/esia/utils.py

def get_timestamp():
    return datetime.datetime.now(pytz.utc).strftime('%Y.%m.%d %H:%M:%S %z').strip()


def smime_sign(certificate_file, private_key_file, data, backend='m2crypto'):
    if backend == 'm2crypto' or backend is None:
        from M2Crypto import SMIME, BIO

        if not isinstance(data, bytes):
            data = bytes(data)

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
    else:
        raise Exception('Unknown cryptography backend. Use openssl or m2crypto value.')


def sign_params(params, certificate_file, private_key_file, backend='m2crypto'):
    plaintext = (params.get('scope', '') + params.get('timestamp', '') +
                 str(params.get('client_id', '')) + params.get('state', ''))
    raw_client_secret = smime_sign(certificate_file, private_key_file, plaintext, backend)
    params.update(
        client_secret=base64.urlsafe_b64encode(raw_client_secret).decode('utf-8'),
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

    def get_user_details(self, response):
        return {'username': response['email'],
                'email': response['email'],
                'fullname': response['fullname'],
                'first_name': response['first_name'],
                'last_name': response['last_name']}

    def user_data(self, access_token, *args, **kwargs):
        id_token = kwargs['response']['id_token']
        payload = jwt.decode(id_token, verify=False)
        oid = payload.get('urn:esia:sbj', {}).get('urn:esia:sbj:oid')
        headers = {'Authorization': "Bearer %s" % access_token}

        url = '{base}{info}/{oid}'.format(
            base=self.BASE_URL, info=self.USER_INFO_PATH, oid=oid
        )
        info = self.get_json(url, headers=headers)

        url = '{base}{info}/{oid}/ctts?embed=(elements)'.format(
            base=self.BASE_URL, info=self.USER_INFO_PATH, oid=oid
        )
        contacts = self.get_json(url, headers=headers)

        first_name = info.get('firstName', '')
        last_name = info.get('lastName', '')
        middle_name = info.get('middleName', '')
        fullname = " ".join(filter(None, [first_name, middle_name, last_name]))

        email = ''
        for e in contacts['elements']:
            value = e['value']
            if self.MAIL_REGEX.match(value):
                email = value
                break

        return {'id': oid,
                'email': email,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}
