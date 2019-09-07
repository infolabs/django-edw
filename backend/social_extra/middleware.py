from django.http import HttpResponseRedirect

from social_core.exceptions import AuthCanceled
from social_django.middleware import SocialAuthExceptionMiddleware


class SocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        if isinstance(exception, AuthCanceled) and hasattr(request, 'strategy'):
            return HttpResponseRedirect(request.strategy.session_get('next', '/'))
        else:
            raise exception
