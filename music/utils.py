import os
import tempfile
import subprocess
import json
from typing import Dict, Optional, Union, List, Tuple, Any, Mapping, cast
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Song, LyricLine

try:
    import mutagen
    from mutagen.id3 import ID3
    from mutagen.id3._frames import TIT2, TPE1, TALB, TCON, USLT, TLEN
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import eyed3
    EYED3_AVAILABLE = True
except ImportError:
    EYED3_AVAILABLE = False


def get_audio_metadata(file_path: str) -> Dict[str, Optional[Union[str, int]]]:
    """
    Trích xuất metadata từ file âm thanh
    
    Hỗ trợ các định dạng: MP3, FLAC, M4A, OGG
    
    Trả về dict với các thông tin:
    - title: Tiêu đề bài hát
    - artist: Nghệ sĩ
    - album: Album
    - genre: Thể loại
    - duration: Thời lượng (giây)
    - lyrics: Lời bài hát (nếu có)
    - year: Năm phát hành (nếu có)
    """
    metadata: Dict[str, Optional[Union[str, int]]] = {
        'title': None,
        'artist': None,
        'album': None,
        'genre': None,
        'duration': None,
        'lyrics': None,
        'year': None
    }
    
    if not os.path.exists(file_path):
        return metadata
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Sử dụng mutagen nếu có
    if MUTAGEN_AVAILABLE:
        try:
            if file_ext == '.mp3':
                audio = MP3(file_path, ID3=ID3)
                if audio.tags:
                    metadata['title'] = str(audio.tags.get('TIT2', ''))
                    metadata['artist'] = str(audio.tags.get('TPE1', ''))
                    metadata['album'] = str(audio.tags.get('TALB', ''))
                    metadata['genre'] = str(audio.tags.get('TCON', ''))
                    if 'USLT' in audio.tags:
                        metadata['lyrics'] = str(audio.tags['USLT'].text)
                metadata['duration'] = int(audio.info.length)
                
            elif file_ext == '.flac':
                audio = FLAC(file_path)
                if 'title' in audio:
                    metadata['title'] = audio['title'][0]
                if 'artist' in audio:
                    metadata['artist'] = audio['artist'][0]
                if 'album' in audio:
                    metadata['album'] = audio['album'][0]
                if 'genre' in audio:
                    metadata['genre'] = audio['genre'][0]
                metadata['duration'] = int(audio.info.length)
                
            elif file_ext in ['.m4a', '.mp4']:
                audio = MP4(file_path)
                if '\xa9nam' in audio:
                    metadata['title'] = audio['\xa9nam'][0]
                if '\xa9ART' in audio:
                    metadata['artist'] = audio['\xa9ART'][0]
                if '\xa9alb' in audio:
                    metadata['album'] = audio['\xa9alb'][0]
                if '\xa9gen' in audio:
                    metadata['genre'] = audio['\xa9gen'][0]
                metadata['duration'] = int(audio.info.length)
        except Exception as e:
            print(f"Mutagen error: {str(e)}")
    
    # Sử dụng eyed3 nếu có và là file MP3
    elif EYED3_AVAILABLE and file_ext == '.mp3':
        try:
            audiofile = eyed3.load(file_path)
            if audiofile and audiofile.tag:
                metadata['title'] = audiofile.tag.title
                metadata['artist'] = audiofile.tag.artist
                metadata['album'] = audiofile.tag.album
                metadata['genre'] = audiofile.tag.genre.name if audiofile.tag.genre else None
                for lyrics in audiofile.tag.lyrics:
                    metadata['lyrics'] = lyrics.text
                metadata['year'] = audiofile.tag.recording_date.year if audiofile.tag.recording_date else None
            if audiofile and audiofile.info:
                metadata['duration'] = int(audiofile.info.time_secs)
        except Exception as e:
            print(f"EyeD3 error: {str(e)}")
    
    # Sử dụng ffprobe như phương án dự phòng
    if metadata['duration'] is None:
        try:
            cmd = ['ffprobe', '-i', file_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            metadata['duration'] = int(float(data['format']['duration']))
        except Exception as e:
            print(f"FFprobe error: {str(e)}")
    
    return metadata


def convert_audio_format(input_file: str, output_format: str = 'mp3', bitrate: str = '192k') -> Optional[str]:
    """
    Chuyển đổi định dạng file âm thanh
    
    input_file: Đường dẫn đến file âm thanh đầu vào
    output_format: Định dạng đầu ra (mp3, ogg, m4a, flac)
    bitrate: Bitrate cho file đầu ra
    
    Trả về đường dẫn đến file đã chuyển đổi
    """
    if not os.path.exists(input_file):
        return None
    
    # Tạo tên file đầu ra
    filename = os.path.basename(input_file)
    name, _ = os.path.splitext(filename)
    output_file = os.path.join(tempfile.gettempdir(), f"{name}.{output_format}")
    
    try:
        # Sử dụng ffmpeg để chuyển đổi
        cmd = ['ffmpeg', '-i', input_file, '-ab', bitrate, '-y', output_file]
        subprocess.run(cmd, capture_output=True)
        
        return output_file
    except Exception as e:
        print(f"Error converting audio: {str(e)}")
        return None


def extract_synchronized_lyrics(lyrics_text: Optional[str]) -> List[Tuple[float, str]]:
    """
    Trích xuất lời bài hát đồng bộ từ văn bản
    
    Format hỗ trợ:
    [00:01.00]Line 1
    [00:05.20]Line 2
    
    Trả về list của tuples (thời gian, lời)
    """
    synced_lyrics: List[Tuple[float, str]] = []
    
    if not lyrics_text:
        return synced_lyrics
    
    for line in lyrics_text.split('\n'):
        line = line.strip()
        if line and line.startswith('[') and ']' in line:
            # Tách timestamp và lời
            timestamp_str = line[1:line.find(']')]
            lyric_text = line[line.find(']')+1:].strip()
            
            # Chuyển đổi timestamp sang giây
            try:
                minutes, seconds = timestamp_str.split(':')
                time_seconds = int(minutes) * 60 + float(seconds)
                synced_lyrics.append((time_seconds, lyric_text))
            except:
                continue
    
    # Sắp xếp theo thời gian tăng dần
    synced_lyrics.sort(key=lambda x: x[0])
    return synced_lyrics


def import_synchronized_lyrics(song_id: int, lyrics_text: str) -> bool:
    """
    Nhập lời bài hát đồng bộ vào cơ sở dữ liệu
    
    song_id: ID của bài hát
    lyrics_text: Văn bản lời đồng bộ
    """
    try:
        song = Song.objects.get(id=song_id)
        
        # Xóa lời đồng bộ cũ nếu có
        LyricLine.objects.filter(song=song).delete()
        
        # Trích xuất lời đồng bộ
        synced_lyrics = extract_synchronized_lyrics(lyrics_text)
        
        # Lưu lời đồng bộ mới
        for timestamp, text in synced_lyrics:
            LyricLine.objects.create(
                song=song,
                timestamp=timestamp,
                text=text
            )
        
        # Cập nhật lời không đồng bộ
        plain_lyrics = '\n'.join([line[1] for line in synced_lyrics])
        song.lyrics = plain_lyrics
        song.save(update_fields=['lyrics'])
        
        return True
    except Song.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error importing lyrics: {str(e)}")
        return False


def normalize_audio(file_path: str, target_level: int = -16) -> Optional[str]:
    """
    Chuẩn hóa âm lượng của file âm thanh
    
    file_path: Đường dẫn đến file âm thanh đầu vào
    target_level: Mức âm lượng mục tiêu tính bằng dB LUFS (Loudness Units Full Scale)
    
    Trả về đường dẫn đến file đã được chuẩn hóa âm lượng
    """
    if not os.path.exists(file_path):
        return None
        
    # Tạo tên file đầu ra
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    output_file = os.path.join(tempfile.gettempdir(), f"{name}_normalized{ext}")
    
    try:
        # Sử dụng ffmpeg-normalize (cần đảm bảo đã cài đặt)
        cmd = [
            'ffmpeg', '-i', file_path,
            '-af', f'loudnorm=I={target_level}:LRA=11:TP=-1.5', 
            '-y', output_file
        ]
        subprocess.run(cmd, capture_output=True)
        
        return output_file
    except Exception as e:
        print(f"Error normalizing audio: {str(e)}")
        return None


def get_waveform_data(file_path: str, num_points: int = 100) -> List[float]:
    """
    Tạo dữ liệu waveform từ file âm thanh
    
    file_path: Đường dẫn đến file âm thanh
    num_points: Số điểm dữ liệu trong kết quả
    
    Trả về list của các giá trị biên độ
    """
    if not os.path.exists(file_path):
        return []
    
    try:
        # Sử dụng ffmpeg để xuất waveform dưới dạng raw
        temp_file = os.path.join(tempfile.gettempdir(), 'waveform_data.raw')
        cmd = [
            'ffmpeg', '-i', file_path, '-filter_complex',
            f'aformat=channel_layouts=mono,compand,showwavespic=s={num_points}x32:scale=sqrt',
            '-frames:v', '1', '-y', temp_file
        ]
        subprocess.run(cmd, capture_output=True)
        
        # Đọc dữ liệu raw
        waveform: List[float] = []
        with open(temp_file, 'rb') as f:
            data = f.read()
            step = max(1, len(data) // num_points)
            for i in range(0, len(data), step):
                if i < len(data):
                    value = data[i] / 255.0  # Chuẩn hóa về khoảng [0,1]
                    waveform.append(value)
        
        # Đảm bảo chỉ có num_points điểm dữ liệu
        while len(waveform) > num_points:
            waveform.pop()
        
        return waveform
    except Exception as e:
        print(f"Error generating waveform: {str(e)}")
        return []


def generate_song_recommendations(user, limit=10):
    """
    Tạo danh sách gợi ý bài hát cho người dùng dựa trên lịch sử nghe, bài hát yêu thích,
    và lịch sử tìm kiếm
    
    Args:
        user: Đối tượng người dùng cần tạo gợi ý
        limit: Số lượng bài hát tối đa trả về
        
    Returns:
        List[Song]: Danh sách các bài hát được gợi ý
    """
    from django.db.models import Count, Q
    from django.contrib.auth import get_user_model
    from utils.pylance_helpers import safe_get_related_field
    from .models import Song, SongPlayHistory, Genre, Artist, SearchHistory, Rating
    
    User = get_user_model()
    
    # Lấy các thể loại yêu thích của người dùng từ lịch sử nghe và bài hát đã thích
    favorite_genres = set()
    
    # Thêm thể loại từ bài hát yêu thích
    favorite_songs = safe_get_related_field(user, 'favorite_songs')
    if favorite_songs:
        for song in favorite_songs.all():
            if song.genre:
                favorite_genres.add(song.genre)
    
    # Thêm thể loại từ lịch sử nghe
    play_history = safe_get_related_field(user, 'play_history')
    if play_history:
        for history in play_history.all()[:50]:  # Chỉ xem xét 50 bài hát gần đây nhất
            if history.song.genre:
                favorite_genres.add(history.song.genre)
    
    # Lấy bài hát đã được đánh giá cao (4-5 sao)
    high_rated_songs = Rating.objects.filter(user=user, rating__gte=4).values_list('song_id', flat=True)
    
    # Lấy danh sách ID bài hát đã nghe gần đây để loại trừ
    recent_songs = set()
    if play_history:
        recent_songs = set(play_history.all()[:20].values_list('song_id', flat=True))
    
    # Lấy danh sách ID bài hát đã thích để loại trừ
    favorite_song_ids = set()
    if favorite_songs:
        favorite_song_ids = set(favorite_songs.all().values_list('id', flat=True))
    
    # Lấy từ khóa tìm kiếm gần đây
    recent_searches = SearchHistory.objects.filter(user=user).order_by('-timestamp')[:10]
    search_keywords = [search.query for search in recent_searches]
    
    # Tạo truy vấn gợi ý
    recommendations = Song.objects.exclude(id__in=recent_songs.union(favorite_song_ids))
    
    # Nếu không có bài hát nào sau khi loại trừ (người dùng đã nghe tất cả), lấy bài hát phổ biến
    if recommendations.count() == 0:
        print(f"User {user.username} đã nghe tất cả bài hát, không loại trừ")
        recommendations = Song.objects.all()
    
    # Ưu tiên bài hát có cùng thể loại với thể loại yêu thích
    if favorite_genres:
        genre_filter = Q()
        for genre in favorite_genres:
            genre_filter |= Q(genre__iexact=genre)
        genre_recommendations = recommendations.filter(genre_filter)
        
        # Nếu có đủ bài hát trong thể loại yêu thích
        if genre_recommendations.count() >= limit:
            return list(genre_recommendations.order_by('-play_count')[:limit])
    
    # Ưu tiên bài hát cùng nghệ sĩ với các bài hát yêu thích
    favorite_artists = set()
    if favorite_songs:
        favorite_artists = set(favorite_songs.all().values_list('artist', flat=True))
    
    if favorite_artists:
        artist_filter = Q()
        for artist in favorite_artists:
            artist_filter |= Q(artist__iexact=artist)
        artist_recommendations = recommendations.filter(artist_filter)
        
        if artist_recommendations.count() >= limit // 2:
            return list(artist_recommendations.order_by('-play_count')[:limit // 2]) + \
                   list(recommendations.exclude(id__in=artist_recommendations.values_list('id', flat=True))
                       .order_by('-play_count')[:limit - limit // 2])
    
    # Thêm gợi ý dựa trên từ khóa tìm kiếm
    if search_keywords:
        search_filter = Q()
        for keyword in search_keywords:
            # Tìm trong tiêu đề, nghệ sĩ và album
            search_filter |= Q(title__icontains=keyword) | Q(artist__icontains=keyword) | Q(album__icontains=keyword)
        
        search_recommendations = recommendations.filter(search_filter)
        if search_recommendations.count() > 0:
            # Kết hợp với bài hát phổ biến
            popular_recommendations = recommendations.order_by('-play_count')[:limit - min(limit // 3, search_recommendations.count())]
            return list(search_recommendations[:limit // 3]) + list(popular_recommendations)
    
    # Đảm bảo luôn trả về ít nhất một số bài hát
    popular_songs = recommendations.order_by('-play_count')[:limit]
    if popular_songs.count() > 0:
        return list(popular_songs)
    
    # Nếu vẫn không có gì, trả về bất kỳ bài hát nào
    return list(Song.objects.all().order_by('?')[:limit])


def download_song_for_offline(song, target_dir: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Tải bài hát để sử dụng offline
    
    song: Đối tượng Song cần tải xuống
    target_dir: Thư mục đích để lưu trữ file (nếu None, sẽ sử dụng thư mục mặc định)
    
    Trả về tuple (success, message, file_path):
    - success: Boolean chỉ ra thành công hay thất bại
    - message: Thông báo kết quả
    - file_path: Đường dẫn đến file đã tải xuống (hoặc None nếu thất bại)
    """
    if not song.audio_file:
        return False, "File âm thanh không tồn tại", None
        
    # Tạo tên file
    song_filename = os.path.basename(song.audio_file.name)
    
    # Xác định thư mục đích
    if not target_dir:
        # Sử dụng thư mục tạm nếu không chỉ định
        target_dir = tempfile.gettempdir()
    
    # Đảm bảo thư mục tồn tại
    os.makedirs(target_dir, exist_ok=True)
    
    target_path = os.path.join(target_dir, song_filename)
    
    try:
        # Trong môi trường thực tế, đây là nơi bạn sẽ sao chép file từ storage về local
        # Trong ví dụ này, chúng ta sẽ sử dụng file gốc từ MEDIA_ROOT
        source_path = song.audio_file.path
        
        # Sao chép file
        import shutil
        shutil.copy2(source_path, target_path)
        
        return True, "Tải xuống thành công", target_path
    except Exception as e:
        return False, f"Lỗi khi tải xuống: {str(e)}", None
        
def verify_offline_song(file_path: str) -> bool:
    """
    Kiểm tra một file nhạc đã tải xuống có hợp lệ không
    
    file_path: Đường dẫn đến file âm thanh cần kiểm tra
    
    Trả về True nếu file hợp lệ, False nếu không
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        # Kiểm tra file có phải là file âm thanh hợp lệ không
        cmd = ['ffprobe', '-i', file_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Nếu ffprobe trả về kết quả hợp lệ, file là hợp lệ
        data = json.loads(result.stdout)
        
        # Kiểm tra xem có stream audio không
        has_audio = False
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                has_audio = True
                break
                
        return has_audio
    except:
        return False
        
def get_offline_song_metadata(file_path: str) -> Dict[str, Any]:
    """
    Lấy metadata của file nhạc offline để hiển thị
    
    file_path: Đường dẫn đến file âm thanh
    
    Trả về dict chứa metadata của file
    """
    # Sử dụng hàm get_audio_metadata đã có
    metadata = get_audio_metadata(file_path)
    
    # Tạo dict mới để tránh lỗi typing
    metadata_dict: Dict[str, Any] = {}
    # Sao chép dữ liệu từ metadata gốc
    for key, value in metadata.items():
        metadata_dict[key] = value
        
    # Bổ sung thông tin về file với kiểu dữ liệu rõ ràng
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    metadata_dict['file_size'] = file_size
    metadata_dict['file_size_mb'] = round(file_size / (1024 * 1024), 2)
    
    return metadata_dict 