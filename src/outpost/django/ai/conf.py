from datetime import timedelta

from appconf import AppConf
from django.conf import settings


class AIAppConf(AppConf):
    BACKEND_REQUEST_TIMEOUT = timedelta(seconds=60)
    BACKEND_REQUEST_CHUNK_SIZE = 64

    class Meta:
        prefix = "ai"
