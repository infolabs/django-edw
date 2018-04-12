from social_core.backends.oauth import BaseOAuth2


class EsiaOAuth2(BaseOAuth2):
    name = 'esia'

    def start(self):
        print("ESIA BACKEND")
        raise NotImplementedError('ESIA OAuth2 Backend. Work in progress')
