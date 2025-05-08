import re

from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    StreamingHttpResponse,
)
from requests import Session

from .. import models

session = Session()


class HeaderStreamingHttpResponse(StreamingHttpResponse):
    def __init__(self, *args, headers=None, **kwargs):
        super().__init__(*args, **kwargs)
        if headers:
            for k, v in headers.items():
                self[k] = v


class HeaderHttpResponse(HttpResponse):
    def __init__(self, *args, headers=None, **kwargs):
        super().__init__(*args, **kwargs)
        if headers:
            for k, v in headers.items():
                self[k] = v


class CountingIteratorProxy:
    def __init__(self, original, stop):
        self.original = original
        self.iteration = 0
        self.stop = stop

    def __iter__(self):
        return self

    def __next__(self):
        try:
            value = next(self.original)
        except StopIteration as e:
            self.stop(self.iteration)
            raise e
        self.iteration = self.iteration + 1
        return value


class AuthenticationMixin:

    bearer_token = re.compile(
        r"^Bearer\s+(?P<secret>[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12})$",
        re.IGNORECASE,
    )

    def dispatch(self, request, *args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth:
            return HttpResponseForbidden()
        match = self.bearer_token.match(auth)
        if not match:
            return HttpResponseForbidden()
        try:
            token = models.Token.objects.get(id=match.group("secret"), enabled=True)
        except models.Token.DoesNotExist:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, token=token, **kwargs)
