from django.urls import (
    include,
    path,
)

from . import (
    ollama,
    openai,
)

app_name = "ai"

urlpatterns = [
    path("openai/", include(openai.urlpatterns)),
    path("ollama/", include(ollama.urlpatterns)),
]
