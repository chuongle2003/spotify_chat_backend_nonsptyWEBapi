from django.apps import AppConfig


class MusicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'music'
    
    def ready(self):
        import music.signals  # Đăng ký signals khi app khởi động
