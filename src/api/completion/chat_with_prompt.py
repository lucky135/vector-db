"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

import json
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

from src.api.common.logging.Logger import log
from src.api.common.validations.mandatory_attributes_verifier import (
    MandatoryAttributesVerifier,
)

from src.api.common.validations.malicious_data_verifier import check_malicious_data

# from src.api.common.raf.sensitive_content_verification import(sensitive_content_validator)

from src.api.common.jwt_token.jwt_decode_validation import validate_jwt_token
from src.api.completion.impl.chat_with_prompt_openai import chat_with_prompt_openai
from src.api.common.error_handler.handle_error_response import handle_error_response
from src.api.completion.impl.llm_wrapper import get_openai_api_base

mandatory_attributes_verfier = MandatoryAttributesVerifier(["prompt"])
counter = 0


@api_view(["POST"])
# @validate_jwt_token
@mandatory_attributes_verfier
@check_malicious_data
# @sensitive_content_validator(['prompt'])
def chat_with_prompt(request):
    """
    Generate answer for a question with no context passed in a request.
    The prompt is tailored based on the chose persona
    :paran rest framework.request.Request request: Django REST Framework Request object
    :return: Django JsonResponse object
    :rtype: django.http.response.JsonResponse :raises ValueError
    """

    global counter
    response = {}
    try:
        log.info("Entering into chat_with_prompt service")

        data = json.loads(request.body)
        # user_details: any = request.session["party"]
        user_details: any = {}
        persona: str = data["persona"]
        prompt: str = data["prompt"]
        gpt_model: str = data["model"]
        chat_type: str = data.get("chat_type", "")
        chat_id: str = data.get("chat_id", "")
        prompt_type: str = data.get("prompt_type", "")
        json_format: str = data.get("json_choice")

        if json_format == "yes" and gpt_model in ("gpt-4-turbo", "gpt4"):
            response_format = {"type": "json_object"}
        else:
            response_format = None

        temperature: float = (
            0.7 if data.get("temperature", "") == "" else float(data.get("temperature"))
        )

        max_token_dict = {
            "gpt-4": 3000,
            "gpt-3.5-turbo": 2000,
            "gpt-3.5-turbo-16k": 6000,
            "gpt-4-turbo": 4000,
            "gpt-4-32k": 8000,
            "gpt-4o": 4000,
        }

        max_token: int = int(
            data.get("max_tokens", max_token_dict.get(gpt_model, 3000))
        )

        opt_out: bool = True if data["opt_out"] == "yes" else False
        summary_required: str = data.get("summary_required", "")
        language: str = data["lanaguage"]

        constitutional_ai_princinple: list = (
            None
            if data["constitutional_ai_principle"] == ""
            else list(data["constitutional_ai_principle"])
        )

        system_message: str = (
            "" if data["system_message"] == "" else str(data["system_message"])
        )

        openai_api_key = get_openai_api_base(gpt_model)

        response["text"], response["conversation_id"] = chat_with_prompt_openai(
            prompt=prompt,
            chat_type=chat_type,
            user_details=user_details,
            chat_id=chat_id,
            persona=persona,
            prompt_type=prompt_type,
            gpt_model=gpt_model,
            temperature=temperature,
            max_token=max_token,
            opt_out=opt_out,
            summary_required=summary_required,
            lanaguage=language,
            constitutional_ai_princinple=constitutional_ai_princinple,
            system_message=system_message,
            response_format=response_format,
            openai_api_key=openai_api_key,
        )

        response_message = response["text"]

        if "```json" in response_message:
            start_index = response_message.find("```json")
            response_message = response_message[start_index + len("```json") :]
            end_index = response_message.rfind("```")
            response_message = response_message[: end_index - 1]

        response["text"] = response_message

        response["message"] = "[SUCCESS]: Answer generated successfully"
        log.info(response["message"])
        return JsonResponse(response, status=200)
    except ValueError as err:

        error_code = "ER-PRSMCP-002"
        err_msg = f"ERROR: Unable to generate answer."

        log.error(
            message=f"Valur Error occurred at chat_with_prompt service :: {err}",
            exc_traceback=err.__traceback__,
        )
        return handle_error_response(
            error_message=err_msg, status_code=400, error_code=error_code
        )

    except Exception as err:
        if "This model's maximum context length is" in err.args[0]:
            err_msg = f"Maximum chat token limit is reached, Please start a new chat."
            error_code = "ER-PRSMCP-004"
        elif "However, your message resulted in" in err.args[0]:
            err_msg = f"Response to your prompt is too big! Please refine your prompt, so it can be in model's context window."
            error_code = "ER-PRSMCP-005"
        elif (
            "have exceeded token rate limit of your current OpenAI S0 pricing tier"
            in err.args[0]
        ):
            err_msg = f"API is currently experiencing higher request, please resubmit your prompt later! Please refine your prompt."
            error_code = "ER-PRSMCP-006"
        else:
            err_msg = f"Unable to generate answer."
            error_code = "ER-PRSMCP-007"

        log.error(
            message=f"Error occurred at chat_with_prompt service :: {err}",
            exc_traceback=err.__traceback__,
        )
        return handle_error_response(
            error_message=err_msg, status_code=400, error_code=error_code
        )
