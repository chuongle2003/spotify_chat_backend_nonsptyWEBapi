from django.contrib.auth.models import AbstractUser
from typing import Any, List, Set

# Định nghĩa stub type cho mô hình User mở rộng
class User(AbstractUser):
    favorite_songs: Any  # Đại diện cho RelatedManager của ManyToManyField
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    # Các phương thức khác có thể được định nghĩa nếu cần 