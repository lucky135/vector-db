from os import getenv

from langchain_community.embeddings import OpenAIEmbeddings


def create_embeddings_model(**kwargs):
    try:
        print("748228384723:", kwargs)
        embeddings = OpenAIEmbeddings()
        return embeddings
    except Exception as e:
        print(f"Error creating embeddings model: {e}")
        raise f"Error creating embeddings model: {e}"
