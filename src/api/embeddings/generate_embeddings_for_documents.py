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
from src.api.common.jwt_token.jwt_decode_validation import validate_jwt_token
from src.api.embeddings.impl.generate_embeddings_openai import (
    generate_embdeddings_from_file,
)
from src.api.completion.impl.llm_wrapper import get_openai_api_base

MAX_UPLOADING_DOCUMENT_SIZE = 25000000


@api_view(["POST"])
@csrf_exempt
# @validate_jwt_token
def upload_file(request):
    """
    Generate embeddings for files sent in request
    """
    # Initialize response dictionary at the beginning
    response = {
        "files_uploaded": [],
        "files_not_uploaded": [],
        "message": "",
        "error_code": "",
    }

    try:
        files = request.FILES.getlist("file")

        collection_name = request.POST.get("collection_name")
        require_rows_processing = request.POST.get("require_rows_processing")

        if collection_name is None or collection_name == "":
            collection_name = "langchain_pg_embedding"

        if require_rows_processing is None or require_rows_processing == "":
            require_rows_processing = False

        files_rejected = []
        files_accepted = []

        openai_api_key = get_openai_api_base("text-embedding-ada-002")

        for file in files:
            if file.size >= MAX_UPLOADING_DOCUMENT_SIZE:
                files_rejected.append({"file_name": file.name, "file": file})
            else:
                files_accepted.append({"file_name": file.name, "file": file})

        response = generate_embdeddings_from_file(
            files=[file["file"] for file in files_accepted],
            collection_name=collection_name,
            require_rows_processing=require_rows_processing,
            openai_api_base="",
            openai_api_key=openai_api_key,
            openai_api_version="",
        )

        too_large_documents = [
            {"file_name": file["file_name"]} for file in files_rejected
        ]

        response["files_not_uploaded"].extend(too_large_documents)

        files_not_uploaded_str = ", ".join(
            [item["file_name"] for item in response["files_not_uploaded"]]
        )

        if len(response["files_uploaded"]) == 0:
            errorID = str(uuid.uuid4())
            response["error_code"] = "ER-PGPT-003"
            response["message"] = (
                f"[ERROR]: No embeddings generated for documents {files_not_uploaded_str}. [ERROR ID]: {errorID}. [ERROR CODE]: {response['error_code']}"
            )
            log.info(f"No embeddings generated. - [ERROR ID] - {errorID}")
            return JsonResponse(response, status=500)

        response["message"] = "[SUCCESS]: Embeddings generated."

        if len(response["files_not_uploaded"]) > 0:
            errorID = str(uuid.uuid4())
            response["error_code"] = "ER-PGPT-003"
            response["message"] = (
                f"[ERROR]: No embeddings generated for documents {files_not_uploaded_str}. [ERROR ID]: {errorID}. [ERROR CODE]: {response['error_code']}"
            )
            log.info(f"No embeddings generated. - [ERROR ID] - {errorID}")
            return JsonResponse(response, status=500)

        return JsonResponse(response, status=200)
    except ValueError as err:
        errorID = str(uuid.uuid4())

        if "already exists" in err.args[0]:
            err_msg = f"Documents with same name already exists. [ERROR ID]: {errorID}"
            response["error_code"] = "ER-PGPT-007"
        elif "No embeddings generated for document" in err.args[0]:
            err_msg = f"No embeddings generated for document. [ERROR ID]: {errorID}"
            response["error_code"] = "ER-PGPT-003"
        else:
            response["error_code"] = "ER-PGPT-003"
            response["message"] = (
                f"[ERROR]: Unable to generate documents. [ERROR ID]: {errorID}. [ERROR CODE]: {response['error_code']}"
            )

        log.info(f"No embeddings generated. - [ERROR ID] - {errorID}")

        return JsonResponse(response, status=500)
