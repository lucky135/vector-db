import json
import uuid
import random

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiTypes,
    OpenApiParameter
)

from langchain.docstore.document import Document
from src.api.common.logging.Logger import log
from src.api.common.validations.mandatory_attributes_verifier import (MandatoryAttributesVerifier)
from src.api.embeddings.impl.generate_embeddings_openai import generate_embdedings
from src.api.common.jwt_token.jwt_decode_validation import validate_jwt_token
from src.api.embeddings.impl.generate_embeddings_openai import get_embeddings
from src.api.completion.impl.llm_wrapper import get_openai_api_base

MAX_UPLOADING_DOCUMENT_SIZE=25000000

mandatory_attribute_verifier = MandatoryAttributesVerifier(["text"])


@api_view(["POST"])
@csrf_exempt
#@validate_jwt_token
@mandatory_attribute_verifier
def create_embeddings_for_text(request):
    """
    Generate embeddings for text sent in a request

    Parameters:
    rest_framework.request.Reuest

    return : JsonResponse Object
    """
    response = {}
    try:
        body = json.loads(request.body)
        text = body["text"]
        collection_name = body["collection_name"]

        # Generate unique number to have unique file name else embedding won't generate
        digits = random.sample(range(10), 6)  # Sample 6 unique digits from 0-9
        random_number = int(''.join(map(str, digits)))
        file_name="User_Submitted_"+str(random_number)+".txt"

        docs = [Document(page_content=text, metadata={"source": file_name})]

        response_message = generate_embdedings(
            file_name=file_name, documents=docs, collection_name=collection_name
        )

        print(f"============== response : {response_message}")

        if response_message:
            response["message"] = "[SUCCESS]: Embeddings generated."
        else:
            response["message"] = "[FAILED]: Embeddings generation failed."
        return JsonResponse(response, status=200)
    except Exception as err:
        errorID = str(uuid.uuid4())
        response["error_code"] = "ER-PGPT-003"
        response["message"] = f"[ERROR]: Unable to geenerate embeddings. [ERROR ID]: {errorID}. [ERROR CODE]: {response['error_code']}"
        log.error(
            f"{err} - [ERROR CODE] - {response['error_code']}",
            exc_traceback=err.__traceback__
        )
        return JsonResponse(response, status=500)


@api_view(["POST"])
@csrf_exempt
@validate_jwt_token
@mandatory_attribute_verifier
def get_embeddings_for_documents(request):
    """
    Get embeddings for text sent in a request

    Parameters:
    rest_framework.request.Reuest

    return : JsonResponse Object
    """
    global counter
    response = {}
    try:
        if "file" in request.FILES:
            files = request.FILES.getlist("file")
            if len(files) != 1:
                return JsonResponse(
                    {"message": "[ERROR]: Only one file can be uploaded at a time."}, status=500
                )
        
            file = files[0]

            if file.size >= MAX_UPLOADING_DOCUMENT_SIZE:
                return JsonResponse(
                    {"message": "[ERROR]: File size exceeds maximum limit of 25MB."}, status=500
                )
        
            counter, openai_api_base, openai_api_key, openai_api_version = (
                get_openai_api_base(counter, "text-embedding-ada-002")
            )

            response = get_embeddings(
                file=file,
                file_name=file.name,
                openai_api_base=openai_api_base,
                openai_api_key=openai_api_key,
                openai_api_version=openai_api_version
            )
        elif "text" in request.data:
            text = request.data["text"]
            counter, openai_api_base, openai_api_key, openai_api_version = (
                get_openai_api_base(counter, "text-embedding-ada-002")
            )

            response = get_embeddings(
                text=text.read().decode("utf-8"),
                openai_api_base=openai_api_base,
                openai_api_key=openai_api_key,
                openai_api_version=openai_api_version
            )
        
        if "embeddings" not in response.keys():
            errorID = str(uuid.uuid4())
            response["error_code"] = "ER-PGPT-003"
            response["message"] = f"[ERROR]: No embeddings generated. [ERROR ID]: {errorID}. [ERROR CODE]: {response['error_code']}"
            log.info(
                f"No embeddings generated. - [ERROR ID] - {errorID}")
            return JsonResponse(response, status=500)

        response["message"] = "[SUCCESS]: Embeddings generated."
        return JsonResponse(response, status=200)
    except Exception as err:
        errorID = str(uuid.uuid4())
        response["error_code"] = "ER-PGPT-003"
        response["message"] = f"[ERROR]: Unable to get embeddings. [ERROR ID]: {errorID}. [ERROR CODE]: {response['error_code']}"
        log.error(
            f"{err} - [ERROR CODE] - {response['error_code']}",
            exc_traceback=err.__traceback__
        )
        return JsonResponse(response, status=500)