class SpotifyTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.has_spotify:
            # Kiểm tra và refresh token nếu cần
            if request.user.spotify_token_needs_refresh():
                request.user.refresh_spotify_token()
        
        response = self.get_response(request)
        return response
