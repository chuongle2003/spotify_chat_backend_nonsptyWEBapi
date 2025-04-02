# Quản lý kết nối spotify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from django.conf import settings
import base64
import requests
import json

class SpotifyPublicClient:
    def __init__(self):
        # Sử dụng Client Credentials Flow
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.token = self._get_token()
        self.client = Spotify(auth=self.token)

    def _get_token(self):
        """Lấy access token sử dụng Client Credentials Flow"""
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        result = requests.post(url, headers=headers, data=data)
        if result.status_code == 200:
            json_result = json.loads(result.content)
            return json_result["access_token"]
        else:
            raise Exception(f"Failed to get token: {result.status_code}")

    def search_tracks(self, query, limit=10, market='VN'):
        """
        Tìm kiếm bài hát với các tham số:
        - query: từ khóa tìm kiếm
        - limit: số lượng kết quả (mặc định: 10)
        - market: thị trường (mặc định: 'VN' cho Việt Nam)
        """
        try:
            return self.client.search(
                q=query, 
                type='track', 
                limit=limit,
                market=market
            )
        except Exception as e:
            # Nếu token hết hạn, thử lấy token mới
            self.token = self._get_token()
            self.client = Spotify(auth=self.token)
            return self.client.search(
                q=query, 
                type='track', 
                limit=limit,
                market=market
            )
    
    def get_track(self, track_id, market='VN'):
        """Lấy thông tin bài hát với market cụ thể"""
        try:
            return self.client.track(track_id, market=market)
        except Exception as e:
            self.token = self._get_token()
            self.client = Spotify(auth=self.token)
            return self.client.track(track_id, market=market)
    
    def get_artist(self, artist_id):
        try:
            return self.client.artist(artist_id)
        except Exception as e:
            self.token = self._get_token()
            self.client = Spotify(auth=self.token)
            return self.client.artist(artist_id)
    
    def get_album(self, album_id, market='VN'):
        """Lấy thông tin album với market cụ thể"""
        try:
            return self.client.album(album_id, market=market)
        except Exception as e:
            self.token = self._get_token()
            self.client = Spotify(auth=self.token)
            return self.client.album(album_id, market=market)

class SpotifyClient:
    def __init__(self):
        self.auth_manager = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope='user-read-private user-read-email playlist-read-private playlist-read-collaborative user-read-playback-state user-modify-playback-state'
        )
        self.client = Spotify(auth_manager=self.auth_manager)

    def get_auth_url(self):
        return self.auth_manager.get_authorize_url()

    def get_token(self, code):
        return self.auth_manager.get_access_token(code)

    def get_user_profile(self):
        try:
            return self.client.current_user()
        except Exception as e:
            return None
    
    def search_tracks(self, query, limit=10):
        return self.client.search(q=query,type= 'track',limit = limit)
    
    def get_track(self,track_id):
        return self.client.track(track_id)
    
    def get_user_playlists(self):
        return self.client.current_user_playlists()
    
    def create_playlist(self, name, description='', public=True):
        try:
            user = self.client.current_user()
            if not user:
                raise Exception("Không thể lấy thông tin người dùng Spotify")
            user_id = user['id']
            return self.client.user_playlist_create(
                user_id, 
                name, 
                public=public, 
                description=description
            )
        except Exception as e:
            raise Exception(f"Lỗi khi tạo playlist: {str(e)}")

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        return self.client.playlist_add_items(playlist_id, track_ids)

    def get_recommendations(self, seed_tracks=None, seed_artists=None, limit=20):
        return self.client.recommendations(
            seed_tracks=seed_tracks,
            seed_artists=seed_artists,
            limit=limit
        )

    def get_current_track(self):
        """Lấy thông tin bài hát đang phát"""
        try:
            current_playback = self.client.current_playback()
            if current_playback and current_playback['item']:
                return current_playback['item']
            return None
        except Exception as e:
            raise Exception(f"Error getting current track: {str(e)}")
    