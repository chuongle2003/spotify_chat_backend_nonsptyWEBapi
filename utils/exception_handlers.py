from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback
from django.conf import settings

def custom_exception_handler(exc, context):
    """
    Exception handler tùy chỉnh để xử lý ngoại lệ trong DRF APIs.
    Ghi log chi tiết và trả về thông báo lỗi thân thiện hơn.
    """
    # Ghi log chi tiết về exception
    logger = logging.getLogger('django')
    logger.error(f"Exception in {context['view'].__class__.__name__}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # Sử dụng exception handler mặc định của DRF
    response = exception_handler(exc, context)
    
    # Nếu là 500 error (response = None), tạo response thân thiện hơn
    if response is None:
        response = Response(
            {
                "error": "Lỗi server, vui lòng liên hệ admin",
                "detail": str(exc) if settings.DEBUG else "Internal server error"
            },
            status=status.HTTP_400_BAD_REQUEST  # Trả về 400 thay vì 500 để cung cấp thông tin lỗi
        )
    
    return response 