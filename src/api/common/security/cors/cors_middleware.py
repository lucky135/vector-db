"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

from typing import Any


class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, reqeust):
        response = self.get_response(reqeust)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"

        return response
