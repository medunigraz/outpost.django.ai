import logging
import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.db import transaction
from outpost.django.base.decorators import signal_connect

from . import tasks

logger = logging.getLogger(__name__)


@signal_connect
class Backend(models.Model):
    """
    ## Fields

    ### `id` (`integer`)
    Primary key.

    ### `name` (`string`)
    Name of demo.
    """

    url = models.URLField()
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.url

    def post_save(self, instance, *args, **kwargs):
        pass


class Token(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "campusonline.Organization",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="+",
    )
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Model(models.Model):
    name = models.CharField(primary_key=True, max_length=256)
    enabled = models.BooleanField(default=True)
    size = models.PositiveIntegerField(editable=False, null=True)
    digest = models.CharField(max_length=64, editable=False, null=True)

    def __str__(self):
        return str(self.name)


@signal_connect
class InstalledModel(models.Model):
    backend = models.ForeignKey(Backend, on_delete=models.CASCADE)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    running = models.BooleanField(default=False, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False, null=True)
    info = JSONField(editable=False, null=True)

    class Meta:
        unique_together = (("backend", "model"),)

    def post_save(self, created, *args, **kwargs):
        if not created:
            return
        transaction.on_commit(lambda: tasks.BackendTasks.pull.delay(self.pk))

    def pre_delete(self, *args, **kwargs):
        tasks.BackendTasks.delete.delay(self.backend.pk, self.model.name)


class Usage(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    model = models.ForeignKey(Model, on_delete=models.SET_NULL, null=True)
    on = models.DateTimeField(auto_now_add=True)
    total = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.token}@{self.model}:{self.total}"
