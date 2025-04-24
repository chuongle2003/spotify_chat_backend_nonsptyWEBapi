def user_permissions(request):
    """
    Context processor cung cấp quyền người dùng cho các templates
    """
    if not request.user.is_authenticated:
        return {
            'is_authenticated': False,
            'is_staff': False,
            'is_admin': False,
            'can_manage_content': False,
            'can_manage_users': False,
            'can_manage_playlists': False,
        }
    
    return {
        'is_authenticated': True,
        'is_staff': request.user.is_staff,
        'is_admin': request.user.is_superuser,
        'can_manage_content': request.user.is_content_manager,
        'can_manage_users': request.user.is_user_manager,
        'can_manage_playlists': request.user.is_playlist_manager,
        'username': request.user.username,
    } 