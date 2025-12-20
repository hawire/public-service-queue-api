"""
Custom exception handler for DRF.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework.exceptions import APIException, AuthenticationFailed, PermissionDenied, ValidationError as DRFValidationError

logger = logging.getLogger(__name__)

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'

def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get the view name where exception occurred
    view = context.get('view', None)
    view_name = view.__class__.__name__ if view else 'Unknown'
    
    if response is None:
        # Handle Django's Http404
        if isinstance(exc, Http404):
            logger.warning(f"404 Not Found in {view_name}: {str(exc)}")
            response_data = {
                "error": "Not Found",
                "message": str(exc) or "The requested resource was not found",
                "status_code": 404
            }
            response = Response(response_data, status=status.HTTP_404_NOT_FOUND)
        
        # Handle Django's ValidationError
        elif isinstance(exc, ValidationError):
            logger.warning(f"Validation Error in {view_name}: {exc.message_dict}")
            response_data = {
                "error": "Validation Error",
                "details": exc.message_dict,
                "status_code": 400
            }
            response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle generic exceptions
        else:
            logger.error(f"Unhandled exception in {view_name}: {str(exc)}", exc_info=True)
            response_data = {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "status_code": 500,
                "reference_id": f"ERR_{id(exc)}"  # For support tracking
            }
            # Only show detailed error in debug mode
            if DEBUG: # type: ignore
                response_data["debug"] = str(exc)
            
            response = Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    else:
        # Log known DRF exceptions
        if isinstance(exc, AuthenticationFailed):
            logger.info(f"Authentication failed in {view_name}")
        elif isinstance(exc, PermissionDenied):
            logger.warning(f"Permission denied in {view_name}: {str(exc)}")
        elif isinstance(exc, DRFValidationError):
            logger.warning(f"DRF Validation error in {view_name}: {exc.detail}")
        
        # Add consistent structure to DRF responses
        if isinstance(response.data, dict):
            response.data["status_code"] = response.status_code
            if "error" not in response.data:
                response.data["error"] = exc.__class__.__name__
    
    return response