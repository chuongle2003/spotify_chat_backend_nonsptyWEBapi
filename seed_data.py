# Mã này sẽ tạo dữ liệu mẫu cho ứng dụng
import os
import django
import random
from datetime import datetime, timedelta

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import các models sau khi đã thiết lập Django
from django.contrib.auth import get_user_model
from music.models import Song, Playlist, Album, Genre, Comment, Rating
from chat.models import Message

User = get_user_model()

def create_users():
    """Tạo người dùng mẫu"""
    print("Creating users...")
    users = []
    
    # Tạo admin user nếu chưa tồn tại
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        users.append(admin)
        print("Created admin user")
    
    # Tạo người dùng thường
    test_users = [
        {'username': 'user1', 'email': 'user1@example.com'},
        {'username': 'user2', 'email': 'user2@example.com'},
        {'username': 'user3', 'email': 'user3@example.com'},
    ]
    
    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='password123',
                bio=f"This is {user_data['username']}'s profile"
            )
            users.append(user)
            print(f"Created user: {user.username}")
    
    return users

def create_genres():
    """Tạo các thể loại nhạc"""
    print("Creating genres...")
    genres = []
    genre_names = [
        'Pop', 'Rock', 'Hip Hop', 'R&B', 'Classical',
        'Jazz', 'Electronic', 'Country', 'Folk', 'Indie'
    ]
    
    for name in genre_names:
        genre, created = Genre.objects.get_or_create(
            name=name,
            defaults={'description': f'Music in the {name} genre'}
        )
        genres.append(genre)
        if created:
            print(f"Created genre: {genre.name}")
    
    return genres

def create_albums():
    """Tạo albums mẫu"""
    print("Creating albums...")
    albums = []
    album_data = [
        {'title': 'Greatest Hits', 'artist': 'Various Artists'},
        {'title': 'Summer Vibes', 'artist': 'DJ Cool'},
        {'title': 'Classic Collection', 'artist': 'Orchestra Ensemble'},
        {'title': 'Rock Legends', 'artist': 'Rock Band'},
        {'title': 'Pop Stars', 'artist': 'Pop Group'},
    ]
    
    for data in album_data:
        album, created = Album.objects.get_or_create(
            title=data['title'],
            artist=data['artist'],
            defaults={
                'release_date': datetime.now().date() - timedelta(days=random.randint(1, 1000)),
                'description': f"Amazing album by {data['artist']}"
            }
        )
        albums.append(album)
        if created:
            print(f"Created album: {album.title}")
    
    return albums

def create_songs(users, genres, albums):
    """Tạo các bài hát mẫu"""
    print("Creating songs...")
    songs = []
    song_data = [
        {'title': 'Summer Jam', 'artist': 'DJ Cool', 'genre': 'Pop'},
        {'title': 'Rock Anthem', 'artist': 'Rock Band', 'genre': 'Rock'},
        {'title': 'Classical Symphony', 'artist': 'Orchestra', 'genre': 'Classical'},
        {'title': 'Hip Hop Beat', 'artist': 'MC Rapper', 'genre': 'Hip Hop'},
        {'title': 'Country Road', 'artist': 'Country Singer', 'genre': 'Country'},
        {'title': 'Jazz Improvisation', 'artist': 'Jazz Ensemble', 'genre': 'Jazz'},
        {'title': 'Electronic Beats', 'artist': 'DJ Electro', 'genre': 'Electronic'},
        {'title': 'Folk Tale', 'artist': 'Folk Band', 'genre': 'Folk'},
        {'title': 'R&B Groove', 'artist': 'R&B Singer', 'genre': 'R&B'},
        {'title': 'Indie Vibe', 'artist': 'Indie Band', 'genre': 'Indie'},
    ]
    
    for data in song_data:
        genre = next((g for g in genres if g.name == data['genre']), None)
        user = random.choice(users)
        album = random.choice(albums)
        
        song, created = Song.objects.get_or_create(
            title=data['title'],
            artist=data['artist'],
            defaults={
                'album': album.title,
                'duration': random.randint(180, 300),  # 3-5 minutes
                'genre': data['genre'],
                'uploaded_by': user,
                'play_count': random.randint(0, 1000),
                'likes_count': random.randint(0, 500),
                'lyrics': f"This is a sample lyric for {data['title']}"
            }
        )
        songs.append(song)
        if created:
            print(f"Created song: {song.title}")
    
    return songs

def create_playlists(users, songs):
    """Tạo playlists mẫu"""
    print("Creating playlists...")
    playlists = []
    playlist_names = [
        'My Favorites', 'Workout Mix', 'Chill Vibes', 
        'Party Time', 'Road Trip', 'Study Music'
    ]
    
    for name in playlist_names:
        user = random.choice(users)
        
        playlist, created = Playlist.objects.get_or_create(
            name=name,
            user=user,
            defaults={
                'description': f"{name} - A playlist by {user.username}",
                'is_public': random.choice([True, True, False])  # 2/3 chance of being public
            }
        )
        
        # Add random songs to playlist
        if created:
            playlist_songs = random.sample(songs, min(len(songs), random.randint(3, 8)))
            for song in playlist_songs:
                playlist.songs.add(song)
            
            playlists.append(playlist)
            print(f"Created playlist: {playlist.name} with {playlist.songs.count()} songs")
    
    return playlists

def create_ratings_and_comments(users, songs):
    """Tạo ratings và comments cho songs"""
    print("Creating ratings and comments...")
    
    comments = [
        "Great song!", "Love this track!", "Amazing melody",
        "This is my jam!", "Perfect for my playlist",
        "The lyrics are so meaningful", "Can't stop listening to this",
        "Best song of the year", "This artist is incredible",
        "The beat is fire!"
    ]
    
    # Thêm ratings và comments cho một số songs
    for song in songs:
        for _ in range(random.randint(1, 3)):  # 1-3 ratings per song
            user = random.choice(users)
            
            # Create rating
            rating, created = Rating.objects.get_or_create(
                user=user,
                song=song,
                defaults={'rating': random.randint(3, 5)}  # Ratings 3-5
            )
            
            if created:
                print(f"Created rating: {rating.rating} stars for {song.title}")
            
            # Create comment with 50% probability
            if random.random() < 0.5:
                comment, created = Comment.objects.get_or_create(
                    user=user,
                    song=song,
                    content=random.choice(comments)
                )
                
                if created:
                    print(f"Created comment on {song.title}")

def create_messages(users):
    """Tạo tin nhắn mẫu giữa users"""
    print("Creating messages...")
    
    message_texts = [
        "Hey, how are you?", "Check out this song!", "What are you listening to?",
        "I love your playlists", "Have you heard the new album?",
        "Let's share some music", "This artist is amazing",
        "I'm creating a new playlist", "What's your favorite genre?",
        "Music makes life better"
    ]
    
    # Tạo một số tin nhắn giữa các users
    for _ in range(20):  # 20 messages
        sender = random.choice(users)
        receiver = random.choice([u for u in users if u != sender])
        
        message = Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=random.choice(message_texts),
            message_type='TEXT'
        )
        
        print(f"Created message from {sender.username} to {receiver.username}")

def main():
    """Hàm chính để tạo dữ liệu"""
    try:
        print("Starting seed data creation...")
        
        users = create_users()
        genres = create_genres()
        albums = create_albums()
        songs = create_songs(users, genres, albums)
        playlists = create_playlists(users, songs)
        create_ratings_and_comments(users, songs)
        create_messages(users)
        
        print("Seed data creation completed successfully!")
    except Exception as e:
        print(f"Error creating seed data: {str(e)}")

if __name__ == "__main__":
    main() 