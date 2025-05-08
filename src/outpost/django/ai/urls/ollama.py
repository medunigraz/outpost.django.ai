from django.urls import path

from ..views import ollama

urlpatterns = [
    path(
        "api/generate",
        ollama.GenerateView.as_view(),
        name="generate",
    ),
    path(
        "api/chat",
        ollama.ChatView.as_view(),
        name="chat",
    ),
    path(
        "api/tags",
        ollama.TagsView.as_view(),
        name="tags",
    ),
    path(
        "api/embed",
        ollama.EmbedView.as_view(),
        name="embed",
    ),
]
