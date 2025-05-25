import re
import os
import uuid
import time
import requests
from urllib.parse import urlparse
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
import src.api.extraction.text_loader as text_loader
from src.api.common.logging.Logger import log
from src.api.common.vectorstore.vectorstore import VectorStoreWrapper
from src.api.completion.impl.embedding_model_wrapper import create_embeddings_model

EMBEDDINGS_MODEL_NAME = "text-embedding-ada-002"
CHUNK_SIZE = 5000
CHUNK_OVERLAP = 50


def normalize_text(s, sep_token=" \n "):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r". ,", "", s)
    s = s.replace("..", ".")
    s = s.replace(". .", ".")
    s = s.replace("\n", "")
    s = s.strip()
    return s


def generate_embdedings(
    file_name,
    documents,
    collection_name,
    **kwargs,
):
    """
    Create embeddings for the input text

    Paramters:
    - file_name - The name of input file
    - documents - Input documents

    Return: {} dict
    """

    log.info("Splitting documents")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        model_name=EMBEDDINGS_MODEL_NAME,
    )

    documents = text_splitter.split_documents(documents)
    if len(documents) == 0:
        log.info(f"No text is extracted from the document {file_name}")
        return False

    if len(documents) > 0:
        start_time = time.time()
        vectorstore_obj = VectorStoreWrapper(
            collection_name=collection_name,
            retriever_type="default",
            openai_api_key=kwargs.get("openai_api_key"),
            openai_api_base=kwargs.get("openai_api_base"),
            openai_api_version=kwargs.get("openai_api_version"),
        )

    for document in documents:
        document.page_content = normalize_text(document.page_content)

    print(f"documents length :: {len(documents)}")
    vectorstore_obj.save_embeddings(file_name=file_name, documents=documents)
    end_time = time.time()
    duration = end_time - start_time
    log.info(f"Embeddings created in {duration} seconds successfully..")

    return True


def get_embeddings(
    file=None,
    file_name=None,
    text=None,
    openai_api_base="",
    openai_api_key="",
    openai_api_version="",
):
    """
    Get embeddings for input text

    Parameters:
    - file_name
    - file
    """

    if file_name is not None:
        output = text_loader.load(file, file.name)
        text_data_from_documents = [doc.page_content for doc in output("docs")]
        text_data_str = "\n".join(text_data_from_documents)

        if len(text_data_str) == 0:
            log.info(f"No text has been extracted from the document {file.name}")
            return {"embeddings": []}
    else:
        text_data_str = text

        if len(text_data_str) == 0:
            log.info(f"No text is provided in the input")
            return {"embeddings": []}

    embeddings = create_embeddings_model(
        openai_api_base=openai_api_base,
        openai_api_key=openai_api_key,
        openai_api_version=openai_api_version,
    )

    data = embeddings.embed_query(text_data_str)
    if len(data) == 0:
        log.info(
            f"No embeddings are generated for the provided document/text {file_name}"
        )
        return {"embeddings": []}

    print(len(data))

    return {"embeddings": data}


def generate_embdeddings_from_file(
    files,
    collection_name,
    require_rows_processing=False,
    openai_api_base="",
    openai_api_key="",
    openai_api_version="",
):
    """
    Create embeddings for the input files

    Parameters:
    - files: The list of files to be processed

    Return: {}
    """

    files_uploaded = []
    files_not_uploaded = []

    for file in files:
        output = text_loader.load(file, file.name, require_rows_processing)
        print(f"output text ::: {output}")
        ret = generate_embdedings(
            file.name,
            output["docs"],
            collection_name=collection_name,
            openai_api_base=openai_api_base,
            openai_api_key=openai_api_key,
            openai_api_version=openai_api_version,
        )

        if ret:
            files_uploaded.append({"file_name": file.name})
        else:
            files_not_uploaded.append({"file_name": file.name})

    return {"files_uploaded": files_uploaded, "files_not_uploaded": files_not_uploaded}
