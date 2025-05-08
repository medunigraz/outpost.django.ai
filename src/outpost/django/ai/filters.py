from django_filters.rest_framework import FilterSet

from . import models


class BackendFilter(FilterSet):
    class Meta:
        model = models.Backend
        fields = ("enabled",)
