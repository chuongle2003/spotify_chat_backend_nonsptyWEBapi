def user_permissions(request):
    """
    Context processor cung cấp quyền người dùng cho các templates
    """
    if not request.user.is_authenticated:
        return {
            'is_authenticated': False,
            'is_admin': False,
        }
    
    return {
        'is_authenticated': True,
        'is_admin': request.user.is_admin,
        'username': request.user.username,
    } 