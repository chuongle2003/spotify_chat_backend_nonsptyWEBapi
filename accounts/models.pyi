from django.contrib.auth.models import AbstractUser
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from typing import Any
 
class User(AbstractUser):
    favorite_songs: ManyToManyDescriptor
    following: ManyToManyDescriptor
    followed_playlists: ManyToManyDescriptor 