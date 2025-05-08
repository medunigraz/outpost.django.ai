import logging

from rest_flex_fields import FlexFieldsModelSerializer

from . import models

logger = logging.getLogger(__name__)


class BackendSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = models.Backend
        exclude = ("url",)
