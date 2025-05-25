import json
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiTypes,
    OpenApiParameter,
)

from src.api.common.logging.Logger import log
from src.api.common.validations.mandatory_attributes_verifier import (
    MandatoryAttributesVerifier,
)
from src.api.common.validations.malicious_data_verifier import check_malicious_data
from src.api.common.jwt_token.jwt_decode_validation import validate_jwt_token
from src.api.common.vectorstore.vectorstore import VectorStoreWrapper
from src.api.completion.impl.embedding_model_wrapper import create_embeddings_model
from src.api.completion.impl.llm_wrapper import get_openai_api_base

# Define the mandatory attributes for the request
mandatory_attributes_verifier = MandatoryAttributesVerifier(
    ["query", "collection_name"]
)


@api_view(["POST"])
@csrf_exempt
# @validate_jwt_token
@mandatory_attributes_verifier
@check_malicious_data
def fetch_relevant_embeddings(request):
    """
    Fetch relevant embeddings based on a query

    Parameters:
    - request: The HTTP request object containing a JSON body with:
        - query: The query text to find relevant embeddings for
        - collection_name: The name of the collection to search in
        - file_name_list (optional): List of file names to filter the search
        - top_k (optional): Number of results to return (default 10)
        - score_threshold (optional): Minimum similarity score threshold (default 0.7)

    Returns:
    - JsonResponse: A JSON response with the relevant embeddings
    """
    response = {
        "embeddings": [],
        "metadata": [],
        "documents": [],
        "message": "",
        "error_code": "",
    }

    try:
        data = json.loads(request.body)
        query = data["query"]
        collection_name = data["collection_name"]
        file_name_list = data.get("file_name_list", [])
        top_k = data.get("top_k", 10)
        score_threshold = data.get("score_threshold", 0.7)

        # Create embeddings model
        embeddings_model = create_embeddings_model(
            openai_api_key=get_openai_api_base("text-embedding-ada-002"),
            openai_api_base="",
            openai_api_version="",
        )

        # Create vector store wrapper
        vectorstore_wrapper = VectorStoreWrapper(
            collection_name=collection_name, retriever_type="default"
        )

        # Get collection count to check if there are embeddings
        collection_count = vectorstore_wrapper.get_total_collection_count()

        if collection_count > 0:
            # Create embeddings for the query
            query_embedding = embeddings_model.embed_query(query)

            # Set up search parameters
            search_kwargs = {
                "retriever_threshold": score_threshold,
                "file_name_list": file_name_list,
                "k": top_k,
            }

            # Get a retriever from the vectorstore
            retriever = vectorstore_wrapper.vectorstore.get_retriever(**search_kwargs)

            # Get relevant documents
            docs = retriever.get_relevant_documents(query)

            # Process results
            for doc in docs:
                response["documents"].append(doc.page_content)
                response["metadata"].append(doc.metadata)
                # We don't return actual embedding vectors for security/privacy reasons

            response["message"] = "[SUCCESS]: Relevant embeddings fetched successfully"
            return JsonResponse(response, status=200)
        else:
            response["message"] = "[WARNING]: No embeddings found in collection"
            return JsonResponse(response, status=200)

    except Exception as err:
        error_id = str(uuid.uuid4())

        if "already exists" in str(err):
            error_msg = f"Document with same name already exists."
            response["error_code"] = "ER-PGPT-007"
        else:
            response["error_code"] = "ER-PGPT-003"
            error_msg = f"Unable to fetch relevant embeddings. [ERROR ID]: {error_id}"

        log.error(
            f"{err} - [ERROR CODE] - {response['error_code']}",
            exc_traceback=err.__traceback__,
        )

        response["message"] = (
            f"[ERROR]: {error_msg} [ERROR CODE]: {response['error_code']}"
        )
        return JsonResponse(response, status=500)
