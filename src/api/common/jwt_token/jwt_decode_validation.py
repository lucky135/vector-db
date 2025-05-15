"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

import requests
from os import getenv
from src.api.common.logging.Logger import log
from src.api.common.error_handler.handle_error_response import handle_error_response
from functools import wraps
from src.api.common.constants.constants import API_ENDPOINTS

PARTY_SERVICE_URL = getenv("PARTY_SERVICE_URL")


def validate_jwt_token(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        log.info(f"Entering the validate_jwt_token middleware")
        headers = {}
        auth_header = request.headers.get("Authorization") or request.headers.get(
            "authorization"
        )
        if not auth_header or auth_header == "":
            log.error(
                message=f"Authorization header missing.",
            )
            return handle_error_response(
                error_message="Authorization header missing.", status_code=403
            )

        headers["Authorization"] = auth_header
        payload = {}

        try:
            token_verifier_response = verify_jwt_token(payload, headers)
            if token_verifier_response:
                request.session["party"] = token_verifier_response.get("party")
                log.info(
                    f"Exiting after success from validate_jwt_token {request.session['party']}"
                )
                return view_func(request, *args, **kwargs)
            else:
                return handle_error_response(
                    error_message="Received empty tokenVerifierResponseBody or tokenVerifierResponseBody.partyId",
                    status_code=401,
                )
        except requests.RequestException as req_err:
            log.error(
                f"Request error at validate_jwt_token decorator: {req_err}",
                exc_traceback=req_err.__traceback__,
            )
            return handle_error_response(
                error_message="Error occurred while verifying the authentication token.",
                status_code=401,
            )
        except ValueError as val_err:
            log.error(
                f"Value error at validate_jwt_token decorator: {val_err}",
                exc_traceback=val_err.__traceback__,
            )
            return handle_error_response(
                error_message="Invalid or expired authentication token.",
                status_code=403,
            )
        except Exception as general_err:
            log.error(
                f"Error occurred at validate_jwt_token decorator: {general_err}",
                exc_traceback=general_err.__traceback__,
            )
            return handle_error_response(
                error_message="Internal Server Error.", status_code=500
            )

    return wrapped_view


def verify_jwt_token(payload, headers):
    log.info(f"Entering in token verification accessor.")
    try:
        token_verification_service_url = (
            f"{PARTY_SERVICE_URL}{API_ENDPOINTS['VERIFICATION_ENDPOINT']}"
        )
        response = requests.post(
            token_verification_service_url, json=payload, headers=headers
        )
        response.raise_for_status()
        log.info("Exiting after success from verify_jwt_token accessor.")
        return response.json()
    except requests.RequestException as e:
        log.error(
            f"Error occurred while verifying the token from tokenVerifier service: {e}"
        )
        raise ValueError("Error occurred while verifying the authentication token.")
