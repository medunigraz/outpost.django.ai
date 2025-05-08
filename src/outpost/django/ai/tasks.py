import hashlib
import json
import logging

import requests
from celery import shared_task
from purl import URL

logger = logging.getLogger(__name__)


class BackendTasks:
    @shared_task(
        bind=True,
        ignore_result=True,
        name=f"{__name__}.Backend:installed",
        autoretry_for=(requests.RequestException,),
        retry_kwargs={"max_retries": 5},
        retry_backoff=True,
    )
    def installed(task):
        from . import models

        headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        for model in models.Model.objects.filter(enabled=True):
            name, tag = model.name.split(":")
            with requests.get(
                f"https://registry.ollama.ai/v2/library/{name}/manifests/{tag}",
                headers=headers,
            ) as response:
                m = hashlib.sha256()
                m.update(response.content)
                model.digest = m.hexdigest()
                payload = response.json()
                model.size = payload.get("config").get("size") + sum(
                    (layer.get("size") for layer in payload.get("layers"))
                )
            model.save()

        headers = {
            "Accept": "application/json",
        }
        for backend in models.Backend.objects.filter(enabled=True):
            base = URL(backend.url)
            with requests.get(
                base.path("/api/tags").as_string(), headers=headers
            ) as response:
                response.raise_for_status()
                installed = {
                    m.get("model"): m.get("digest")
                    for m in response.json().get("models")
                }
                for im in backend.installedmodels.filter(model__enabled=True):
                    digest = installed.get(im.model.name)
                    if not digest or digest != im.model.digest:
                        logger.info(
                            f"Model {im.model} not installed or outdated on {backend}, scheduling pull"
                        )
                        BackendTasks.pull.delay(im.pk)

    @shared_task(
        bind=True,
        ignore_result=True,
        name=f"{__name__}.Backend:running",
        autoretry_for=(requests.RequestException,),
        retry_kwargs={"max_retries": 5},
        retry_backoff=True,
    )
    def running(task):
        from . import models

        headers = {
            "Accept": "application/json",
        }
        for backend in models.Backend.objects.filter(enabled=True):
            base = URL(backend.url)
            with requests.get(
                base.path("/api/ps").as_string(), headers=headers
            ) as response:
                response.raise_for_status()
                running = {m.get("model") for m in response.json().get("models")}
                for im in backend.installedmodels.filter(model__enabled=True):
                    if im.model.name in running:
                        if im.running:
                            continue
                        im.running = True
                    else:
                        if not im.running:
                            continue
                        im.running = False
                    im.save()

    @shared_task(
        bind=True,
        ignore_result=True,
        name=f"{__name__}.Backend:pull",
        autoretry_for=(requests.RequestException,),
        retry_kwargs={"max_retries": 5},
        retry_backoff=True,
    )
    def pull(task, pk):
        from . import models

        try:
            im = models.InstalledModel.objects.get(pk=pk)
        except models.InstalledModel.DoesNotExist:
            logger.error(f"Could not find model {pk}")
            return
        base = URL(im.backend.url)
        logger.info(f"Pulling model {im.model} on {im.backend}")
        with requests.post(
            base.path("/api/pull").as_string(),
            json={"model": im.model.name},
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                payload = json.loads(line)
                task.update_state(state="PROGRESS", meta=payload)
        with requests.post(
            base.path("/api/show").as_string(), json={"model": im.model.name}
        ) as response:
            response.raise_for_status()
            im.info = response.json()
            im.save()

    @shared_task(
        bind=True,
        ignore_result=True,
        name=f"{__name__}.Backend:delete",
        autoretry_for=(requests.RequestException,),
        retry_kwargs={"max_retries": 5},
        retry_backoff=True,
    )
    def delete(task, pk, name):
        from . import models

        try:
            backend = models.Backend.objects.get(pk=pk)
        except models.Backend.DoesNotExist:
            logger.error(f"Could not find backend {pk}")
            return
        base = URL(backend.url)
        logger.info(f"Deleting model {name} from {backend}")
        with requests.delete(
            base.path("/api/delete").as_string(),
            json={"model": name},
        ) as response:
            response.raise_for_status()
