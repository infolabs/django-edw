Django EDW
==========
Example settings for `social_extra` ESIA backend:
```python
AUTHENTICATION_BACKENDS = (
    ...
    'social_extra.backends.EsiaOAuth2',
    ...
)
SOCIAL_AUTH_ESIA_URL = 'https://esia-portal1.test.gosuslugi.ru'
SOCIAL_AUTH_ESIA_KEY = 'YOUR-KEY'
SOCIAL_AUTH_ESIA_SCOPE = ['openid', 'email', 'fullname', 'mobile']
SOCIAL_AUTH_ESIA_CERTIFICATE = '/path/to/esia_cert.crt'
SOCIAL_AUTH_ESIA_PRIVKEY = '/path/to/esia.key'
```
