from outpost.django.base.decorators import docstring_format
from rest_flex_fields.views import FlexFieldsMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from . import (
    models,
    serializers,
)


@docstring_format(
    model=models.Backend.__doc__, serializer=serializers.BackendSerializer.__doc__
)
class BackendViewSet(FlexFieldsMixin, ReadOnlyModelViewSet):
    """
    List backends.

    {model}
    {serializer}
    """

    queryset = models.Backend.objects.all()
    serializer_class = serializers.BackendSerializer
    permission_classes = (IsAuthenticated,)
    permit_list_expands = ("models",)
