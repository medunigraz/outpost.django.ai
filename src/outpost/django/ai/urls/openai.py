from django.urls import path

from ..views import openai

urlpatterns = [
    path(
        "v1/chat/completions",
        openai.ChatCompletionsView.as_view(),
        name="chat-completions",
    ),
    path(
        "v1/completions",
        openai.CompletionsView.as_view(),
        name="completions",
    ),
    path(
        "v1/models",
        openai.ModelsView.as_view(),
        name="models",
    ),
    path(
        "v1/models/<str:name>",
        openai.ModelsView.as_view(),
        name="models",
    ),
    path(
        "v1/embeddings",
        openai.EmbeddingsView.as_view(),
        name="embeddings",
    ),
]
