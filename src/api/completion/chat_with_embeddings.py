import json
import os
import uuid
from collections import defaultdict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiExample,
)

from src.api.common.validations.mandatory_attributes_verifier import (
    MandatoryAttributesVerifier,
)

from src.api.common.validations.malicious_data_verifier import check_malicious_data
from src.api.common.raf.sensitive_content_verification import (
    sensitive_content_validator,
)

from src.api.common.logging.Logger import log
from src.api.common.jwt_token.jwt_decode_validation import validate_jwt_token
from src.api.completion.impl.chat_with_embeddings_openai import (
    chat_with_embedding_openai,
)
from src.api.common.database.store_handler import store_handler
from src.api.common.vectorstore.vectorstore import VectorStoreWrapper
from src.api.common.error_handler.handle_error_response import handle_error_response
from src.api.completion.impl.llm_wrapper import get_openai_api_base

mandatory_attributes_verifier = MandatoryAttributesVerifier(["prompt", "index_search"])


@api_view(["POST"])
@csrf_exempt
# @validate_jwt_token
@mandatory_attributes_verifier
@check_malicious_data
def chat_with_embedding(request):
    response = {}
    try:
        data = json.loads(request.body)
        prompt: str = data["prompt"]
        chat_id: str = data["chat_id"]
        index_search: str = data["index_search"]
        gpt_model: str = data["gpt_model"]
        collection_name: str = data["collection_name"]

        if collection_name is None or collection_name == "":
            collection_name = "langchain_pg_embedding"

        temperature: float = (
            0.7 if data["temperature"] == "" else float(data["temperature"])
        )

        chain_type = data.get("chain_type", "")
        retriever_threshold_type = data.get("retriever_threshold", "Medium")
        retriever_type = data.get("retriever_type", "precise")

        json_format: str = data.get("json_choice")
        if json_format == "yes" and gpt_model in ("gpt-4-turbo", "gpt-4", "gpt-4o"):
            response_format = {"type": "json_pbject"}
        else:
            response_format = None

        # hardcoding it as of now coz we are using gpt-4o
        max_tokens: int = 4000

        chat_type: str = data["chat_type"]
        file_name_list: list = data["file_name_list"]
        language: str = data["language"]

        opt_out: bool = True if data["opt_out"] == "yes" else False

        system_message: str = data.get("system_message", "")

        openai_api_key = get_openai_api_base(gpt_model)

        frequency_penalty: int = data.get("frequency_penalty", 0)
        presence_penalty: int = data.get("presence_penalty", 0)

        (
            response["text"],
            response["sources"],
            response["conversation_id"],
            response["sources_data"],
        ) = chat_with_embedding_openai(
            prompt=prompt,
            chat_id=chat_id,
            index_search=index_search,
            gpt_model=gpt_model,
            chat_type=chat_type,
            max_tokens=max_tokens,
            temperature=temperature,
            persona="HSN_FINDER",
            prompt_type="HSN_FINDER",
            retriever_threshold_type=retriever_threshold_type,
            retriever_type=retriever_type,
            file_name_list=file_name_list,
            chain_type=chain_type,
            opt_out=opt_out,
            language=language,
            system_message=system_message,
            response_format=response_format,
            openai_api_base="",
            openai_api_key=openai_api_key,
            openai_api_version="",
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            collection_name=collection_name,
        )

        print(f"chat with embedding executed successfully")

        response_message = response["text"]

        print(f"response_message :: {response_message}")

        if "```json" in response_message:
            start_index = response_message.find("```json")
            response_message = response_message[start_index + len("```json") :]
            end_index = response_message.rfind("```")
            response_message = response_message[: end_index - 1]

        response["text"] = response_message

        response["message"] = "[SUCCESS]: Answer questions successfully"
        return JsonResponse(response, status=200)
    except Exception as err:
        errorID = str(uuid.uuid4())

        if "already exists" in err.args[0]:
            err_msg = f"Document with same name already exists."
            error_code = "ER-PRSMCP-007"
        elif "This model's maximum context length is" in err.args[0]:
            err_msg = f"Maximum chat tokenn limit is reached, please start a new chat"
            error_code = "ER-PRSMCP-004"
        elif ("have exceeded token rate limit of your current OpenAI") in err.args[0]:
            err_msg = f"API are experiencing higher request, please resubmit your request later."
            error_code = "ER-PRSMCP-006"
        else:
            err_msg = f"Unable to answer question."
            error_code = "ER-PRSMCP-002"

        log.error(
            message=f"Error occurred at chat_with_embeddings service :: {err}",
            exc_traceback=err.__traceback__,
        )
        return handle_error_response(
            error_message=err_msg, status_code=400, error_code=error_code
        )


@api_view(["POST"])
@csrf_exempt
# @validate_jwt_token
@mandatory_attributes_verifier
@check_malicious_data
def chat_with_embedding_adv(request):
    response = {}
    try:
        data = json.loads(request.body)
        prompt: str = data["prompt"]
        chat_id: str = data["chat_id"]
        index_search: str = data["index_search"]
        gpt_model: str = data["gpt_model"]
        collection_name: str = data["collection_name"]

        if collection_name is None or collection_name == "":
            collection_name = "langchain_pg_embedding"

        temperature: float = (
            0.7 if data["temperature"] == "" else float(data["temperature"])
        )

        persona: str = data["persona"]
        prompt_type: str = data["prompt_type"]

        chain_type = data.get("chain_type", "")
        retriever_threshold_type = data.get("retriever_threshold", "Medium")
        retriever_type = data.get("retriever_type", "precise")

        json_format: str = data.get("json_choice")
        if json_format == "yes" and gpt_model in ("gpt-4-turbo", "gpt-4", "gpt-4o"):
            response_format = {"type": "json_pbject"}
        else:
            response_format = None

        # hardcoding it as of now coz we are using gpt-4o
        max_tokens: int = 4000

        chat_type: str = data["chat_type"]
        file_name_list: list = data["file_name_list"]
        language: str = data["language"]

        opt_out: bool = True if data["opt_out"] == "yes" else False

        system_message: str = data.get("system_message", "")

        openai_api_key = get_openai_api_base(gpt_model)

        frequency_penalty: int = data.get("frequency_penalty", 0)
        presence_penalty: int = data.get("presence_penalty", 0)

        (
            response["text"],
            response["sources"],
            response["conversation_id"],
            response["sources_data"],
        ) = chat_with_embedding_openai(
            prompt=prompt,
            chat_id=chat_id,
            index_search=index_search,
            gpt_model=gpt_model,
            chat_type=chat_type,
            max_tokens=max_tokens,
            persona=persona,
            prompt_type=prompt_type,
            temperature=temperature,
            retriever_threshold_type=retriever_threshold_type,
            retriever_type=retriever_type,
            file_name_list=file_name_list,
            chain_type=chain_type,
            opt_out=opt_out,
            language=language,
            system_message=system_message,
            response_format=response_format,
            openai_api_base="",
            openai_api_key=openai_api_key,
            openai_api_version="",
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            collection_name=collection_name,
        )

        print(f"chat with embedding executed successfully")

        response_message = response["text"]

        print(f"response_message :: {response_message}")

        if "```json" in response_message:
            start_index = response_message.find("```json")
            response_message = response_message[start_index + len("```json") :]
            end_index = response_message.rfind("```")
            response_message = response_message[: end_index - 1]

        response["text"] = response_message

        response["message"] = "[SUCCESS]: Answer questions successfully"
        return JsonResponse(response, status=200)
    except Exception as err:
        errorID = str(uuid.uuid4())

        if "already exists" in err.args[0]:
            err_msg = f"Document with same name already exists."
            error_code = "ER-PRSMCP-007"
        elif "This model's maximum context length is" in err.args[0]:
            err_msg = f"Maximum chat tokenn limit is reached, please start a new chat"
            error_code = "ER-PRSMCP-004"
        elif ("have exceeded token rate limit of your current OpenAI") in err.args[0]:
            err_msg = f"API are experiencing higher request, please resubmit your request later."
            error_code = "ER-PRSMCP-006"
        else:
            err_msg = f"Unable to answer question."
            error_code = "ER-PRSMCP-002"

        log.error(
            message=f"Error occurred at chat_with_embeddings service :: {err}",
            exc_traceback=err.__traceback__,
        )
        return handle_error_response(
            error_message=err_msg, status_code=400, error_code=error_code
        )
