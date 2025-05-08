import json
import logging

from braces.views import (
    CsrfExemptMixin,
    JSONResponseMixin,
)
from django.http import (
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.views import View
from purl import URL
from requests import (
    Request,
    RequestException,
)

from .. import models
from ..conf import settings
from . import (
    AuthenticationMixin,
    CountingIteratorProxy,
    HeaderHttpResponse,
    HeaderStreamingHttpResponse,
    session,
)

logger = logging.getLogger(__name__)


class GenerateView(CsrfExemptMixin, AuthenticationMixin, View):
    def post(self, request, token, *args, **kwargs):
        body = json.loads(request.body)
        name = body.get("model")
        stream = body.get("stream", True)
        im = (
            models.InstalledModel.objects.filter(
                model__name=name, model__enabled=True, backend__enabled=True
            )
            .order_by("?")
            .first()
        )
        if not im:
            logger.warning(f"Unknown model {name} requested")
            return HttpResponseNotFound()
        bereq = Request(
            request.method,
            URL(im.backend.url)
            .path_segments(URL(request.path).path_segments()[2:])
            .as_string(),
            data=request.body,
            headers=request.headers,
        )
        try:
            with session.send(
                bereq.prepare(),
                stream=stream,
                timeout=settings.AI_BACKEND_REQUEST_TIMEOUT.total_seconds(),
            ) as response:
                response.raise_for_status()
                if stream:
                    iterator = CountingIteratorProxy(
                        response.iter_content(settings.AI_BACKEND_REQUEST_CHUNK_SIZE),
                        stop=lambda x: models.Usage.objects.create(
                            model=im.model, token=token, total=x
                        ),
                    )
                    return HeaderStreamingHttpResponse(
                        iterator, headers=response.headers
                    )
                else:
                    payload = json.loads(response.content)
                    models.Usage.objects.create(
                        model=im.model,
                        token=token,
                        total=payload.get("prompt_eval_count")
                        + payload.get("eval_count"),
                    )
                    return HeaderHttpResponse(
                        response.content, headers=response.headers
                    )
        except RequestException as e:
            logger.error(f"Failed to fetch response from backend {im.backend}: {e}")
        return HttpResponseServerError()


class ChatView(CsrfExemptMixin, AuthenticationMixin, View):
    def post(self, request, token, *args, **kwargs):
        body = json.loads(request.body)
        name = body.get("model")
        stream = body.get("stream", True)
        im = (
            models.InstalledModel.objects.filter(
                model__name=name, model__enabled=True, backend__enabled=True
            )
            .order_by("?")
            .first()
        )
        if not im:
            logger.warning(f"Unknown model {name} requested")
            return HttpResponseNotFound()
        bereq = Request(
            request.method,
            URL(im.backend.url)
            .path_segments(URL(request.path).path_segments()[2:])
            .as_string(),
            data=request.body,
            headers=request.headers,
        )
        try:
            with session.send(
                bereq.prepare(),
                stream=stream,
                timeout=settings.AI_BACKEND_REQUEST_TIMEOUT.total_seconds(),
            ) as response:
                response.raise_for_status()
                if stream:
                    iterator = CountingIteratorProxy(
                        response.iter_content(settings.AI_BACKEND_REQUEST_CHUNK_SIZE),
                        stop=lambda x: models.Usage.objects.create(
                            model=im.model, token=token, total=x
                        ),
                    )
                    return HeaderStreamingHttpResponse(
                        iterator, headers=response.headers
                    )
                else:
                    payload = json.loads(response.content)
                    models.Usage.objects.create(
                        model=im.model,
                        token=token,
                        total=payload.get("prompt_eval_count")
                        + payload.get("eval_count"),
                    )
                    return HeaderHttpResponse(
                        response.content, headers=response.headers
                    )
        except RequestException as e:
            logger.error(f"Failed to fetch response from backend {im.backend}: {e}")
        return HttpResponseServerError()


class TagsView(CsrfExemptMixin, AuthenticationMixin, JSONResponseMixin, View):
    def serialize(self, model):
        return {
            "name": model.name,
            "model": model.name,
            "digest": model.digest,
            "size": model.size,
        }

    def get(self, request, *args, name=None, **kwargs):
        models = [self.serialize(m) for m in models.Model.objects.filter(enabled=True)]
        return self.render_json_object_response(models)


class EmbedView(CsrfExemptMixin, AuthenticationMixin, View):
    def post(self, request, token, *args, **kwargs):
        body = json.loads(request.body)
        name = body.get("model")
        im = (
            models.InstalledModel.objects.filter(
                model__name=name, model__enabled=True, backend__enabled=True
            )
            .order_by("?")
            .first()
        )
        if not im:
            logger.warning(f"Unknown model {name} requested")
            return HttpResponseNotFound()
        bereq = Request(
            request.method,
            URL(im.backend.url)
            .path_segments(URL(request.path).path_segments()[2:])
            .as_string(),
            data=request.body,
            headers=request.headers,
        )
        try:
            with session.send(
                bereq.prepare(),
                timeout=settings.AI_BACKEND_REQUEST_TIMEOUT.total_seconds(),
            ) as response:
                response.raise_for_status()
                payload = response.json()
                models.Usage.objects.create(
                    model=im.model, token=token, total=payload.get("prompt_eval_count")
                )
                return HeaderHttpResponse(response.content, headers=response.headers)
        except RequestException as e:
            logger.error(f"Failed to fetch response from backend {im.backend}: {e}")
        return HttpResponseServerError()
