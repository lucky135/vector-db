
import uuid
from src.api.common.logging.Logger import log
from django.http import JsonResponse

def handle_error_response(error_message, status_code, error_code=""):
    """
    Helper function to handle error responses.
    """
    error_id = str(uuid.uuid4())
    log.error(f"{error_message} - [ERROR_ID]: {error_id}")
    
    response_data = {
        "message": f"[ERROR]: {error_message} - [ERROR ID]: {error_id} - [ERROR CODE]: {error_code} if error_code else ''",
        "error_id": error_id,
    }
    if error_code:
        response_data["error_code"] = error_code
        
    return JsonResponse(
        response_data,
        status=status_code
    )