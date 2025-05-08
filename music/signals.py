import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Song


@receiver(post_delete, sender=Song)
def delete_song_files(sender, instance, **kwargs):
    """
    Xử lý tự động xóa các file khi bài hát bị xóa khỏi database.
    Được gọi tự động sau khi xóa instance Song.
    """
    # Xóa file âm thanh
    if instance.audio_file:
        if os.path.isfile(instance.audio_file.path):
            try:
                os.remove(instance.audio_file.path)
            except (FileNotFoundError, PermissionError) as e:
                print(f"Không thể xóa file âm thanh: {e}")
    
    # Xóa file ảnh bìa
    if instance.cover_image:
        if os.path.isfile(instance.cover_image.path):
            try:
                os.remove(instance.cover_image.path)
            except (FileNotFoundError, PermissionError) as e:
                print(f"Không thể xóa file ảnh bìa: {e}") 