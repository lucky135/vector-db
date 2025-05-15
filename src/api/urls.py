from django.urls import path

from src.api.completion.chat_with_prompt import chat_with_prompt
from src.api.embeddings.generate_embeddings_for_documents import upload_file
from src.api.embeddings.generate_embeddings_for_text import get_embeddings_for_documents
from src.api.completion.chat_with_embeddings import (
    chat_with_embedding,
    chat_with_embedding_adv,
)
from src.api.embeddings.generate_embeddings_for_text import create_embeddings_for_text

urlpatterns = [
    path("vectorcopilot/chat/completion/", view=chat_with_prompt),
    path("vectorcopilot/files/upload/", view=upload_file),
    path("vectorcopilot/embeddings", view=get_embeddings_for_documents),
    path(
        "vectorcopilot/chat/completion/embeddings/prompt/hsnfinder/",
        view=chat_with_embedding,
    ),
    path("vectorcopilot/embeddings/generate/product/", view=create_embeddings_for_text),
    path(
        "vectorcopilot/chat/completion/embeddings/prompt/", view=chat_with_embedding_adv
    ),
]
