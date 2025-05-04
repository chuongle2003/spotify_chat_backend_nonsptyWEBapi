class APIDeprecationMiddleware:
    """
    Middleware để thêm thông báo deprecation vào các API cũ
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Chỉ xử lý các request đến /api/ nhưng không phải /api/v1/
        if (request.path.startswith('/api/') and 
            not request.path.startswith('/api/v1/') and 
            not request.path.startswith('/api/schema/') and
            not request.path.startswith('/api/docs/') and
            not request.path.startswith('/api/documentation/')):
            
            # Nếu là API JSON response, thêm warning header
            if hasattr(response, 'data') and isinstance(response.data, dict):
                # Đối với DRF Response
                if 'warning' not in response.data:
                    response['X-API-Deprecated'] = 'True'
                    response['X-API-New-Path'] = request.path.replace('/api/', '/api/v1/')
            else:
                # Đối với các response khác
                response['X-API-Deprecated'] = 'True'
                response['X-API-New-Path'] = request.path.replace('/api/', '/api/v1/')
                
        return response 