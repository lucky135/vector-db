"""Decorator class to check for sql injection and javascript injection in request"""

"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""
import json
import re
from django.http import JsonResponse
from src.api.common.logging.Logger import log


def check_malicious_data(view_func):
    def wrapper(request, *args, **kwargs):
        # Check if request content type is JSON
        if request.content_type == "application/json":
            try:
                data = request.body.decode("utf-8")
                data_dict = json.loads(data)
            except:
                return JsonResponse({"error": "Invalid JSON data"}, status=400)
        # check if request content type is form data or multipart form data
        elif request.content_type in [
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]:
            data_dict = request.POST
        else:
            return JsonResponse({"ERROR": "Invalid content type"}, status=400)

        # Regular expression pattern to detect SQL injection
        sql_injection_pattern = re.compile(
            r"(\b(?:SELECT|UPDATE|DELETE|INSERT|DROP|ALTER|CREATE|EXEC|UNION|ALL|ANY|TABLE|FROM|WHERE|AND|OR|NOT|NULL|HAVING|JOIN|TRUNCATE|EXECUTE|--|#|;|'|\"|\*)\b)",
            re.IGNORECASE,
        )

        # Regular expression pattern to check javascript injection
        js_injection_pattern = re.compile(
            r"(\b(?:<script\b|<\/script>|javascript:|onerror\s*=|onload\s*=|onclick\s*=|alert\s*\(|console\.log\s*\(|eval\s*\(|setTimeout\s*\(|setInterval\s*\(|document\.|window\.|innerHTML\b|outerHTML\b|href\s*=|src\s*=|location\s*=|cookie\s*=)\b)",
            re.IGNORECASE,
        )

        # Check for malicious data in the request
        for key, value in data_dict.items():
            if sql_injection_pattern.search(str(value)):
                log.info("ERROR: SQL Injection detected")
            elif js_injection_pattern.search(str(value)):
                log.info("ERROR: Javascript Injection detected")
                return JsonResponse(
                    {"ERROR:": "Javascript Injection detected"}, status=400
                )
        return view_func(request, *args, **kwargs)

    return wrapper
