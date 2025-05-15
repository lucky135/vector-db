"""
Base decorator to check for insensitive content
"""

"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""
import json
import threading
from os import getenv
from functools import wraps

import openai
from django.http import JsonResponse
from better_profanity import profanity

from src.api.common.logging.Logger import log


openai_api_type = getenv("OPENAI_API_TYPE")


def sensitive_content_validator(attributes):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                body_data = json.loads(request.body.decode("utf-8"))
            except ValueError:
                return JsonResponse({"ERROR": "Invalid Json data"}, status=400)

            if not openai.api_key:
                return JsonResponse(
                    {"ERROR": f"No, {openai_api_type.capitalize()} OpenAI Key"},
                    status=400,
                )

            for attribute in attributes:
                value = body_data.get(attribute)
                if not value:
                    continue

                log.info(
                    f"Profanity is called if there is any sensitive content identified"
                )
                if isinstance(value, str) and profanity.contains_profanity(value):
                    log.info(
                        f"Insensitive content identified in an incoming API using profanity"
                    )
                    # Functionality can be added in future to store the violations in the database

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


local_data = threading.local()


def set_request(request):
    local_data.request = request


def get_request():
    return getattr(local_data, "request", None)


def output_sensitive_content_validator(func):
    """
    Decorator to check sensitive info in response
    """

    @wraps(func)
    def _wrapped_view(*args, **kwargs):
        result = func(*args, **kwargs)
        if not openai.api_key:
            return JsonResponse(
                {"ERROR": f"No, {openai_api_type.capitalize()} OpenAI Key"}, status=400
            )

        censored_message = "Censored due to offensive content."
        request = get_request()

        if request and "user_details" in request.session:
            log.info(
                f"Profanity is called if there is any sensitive content identified"
            )
            if isinstance(result, str) and profanity.contains_profanity(result):
                log.info(
                    f"Insensitive content identified in an incoming API using profanity"
                )
                # Functionality can be added in future to store the violations in the database

                return censored_message
        return result

    return _wrapped_view
