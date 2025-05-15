"""Decorator class to check mandatory attributes in incoming request"""

"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

import json
from functools import wraps
from django.http import JsonResponse
from src.api.common.logging.Logger import log


class MandatoryAttributesVerifier:
    """
    Decorator that validates that the incoming request has all mandatory parameters.
    This check is applied to all API endpoints making the code cnetralized and easy to apply.

    :param [List] parameter_names: list of parameters to be checked
    """

    def __init__(self, parameter_names):
        self.parameter_names = parameter_names

    def __call__(self, view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            request_body = {}

            # Check if request content type is JSON
            if request.content_type == "application/json":
                try:
                    data = request.body.decode("utf-8")
                    request_body = json.loads(data)
                except:
                    return JsonResponse({"error": "Invalid request body"}, status=400)
            # check if request content type is form data or multipart form data
            elif request.content_type in [
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            ]:
                request_body = request.POST
            else:
                return JsonResponse({"ERROR": "Invalid content type"}, status=400)

            request_data = {**request_body}
            for parameter in self.parameter_names:
                parameter_value = request_data.get(parameter)
                if not parameter_value:
                    message = f"Missing mandatory attriutes - {parameter}"
                    log.info(message)
                    return JsonResponse({"ERROR: message"}, status=401)

            return view_func(request, *args, **kwargs)

        return _wrapped_view
