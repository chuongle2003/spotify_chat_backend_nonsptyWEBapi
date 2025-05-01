import os
import tempfile
import subprocess
import json
from typing import Dict, Optional, Union, List, Tuple
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
    
    file_path: Đường dẫn đến file âm thanh
    target_level: Mức âm lượng mục tiêu tính bằng dB LUFS
    
    Trả về đường dẫn đến file đã chuẩn hóa
    """
    if not os.path.exists(file_path):
        return None
    
    # Tạo tên file đầu ra
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    output_file = os.path.join(tempfile.gettempdir(), f"{name}_normalized{ext}")
    
    try:
        # Sử dụng ffmpeg với loudnorm filter
        cmd = [
            'ffmpeg', '-i', file_path,
            '-af', f'loudnorm=I={target_level}:TP=-1.5:LRA=11',
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