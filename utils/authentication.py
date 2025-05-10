from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """
    Lớp xác thực JWT tùy chỉnh luôn trả về lỗi dạng JSON 
    thay vì redirect đến trang đăng nhập
    """
    
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except AuthenticationFailed as e:
            # Ghi log lỗi xác thực
            logger.warning(f"Authentication failed: {str(e)}")
            # Không làm thay đổi cách xử lý ngoại lệ mặc định,
            # chỉ đảm bảo sẽ luôn trả về lỗi dạng JSON
            raise e

    def authenticate_header(self, request):
        """
        Trả về tiêu đề xác thực thích hợp cho kết quả WWW-Authenticate
        """
        return 'Bearer realm="api"' 