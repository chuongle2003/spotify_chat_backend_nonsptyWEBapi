# Hướng dẫn sử dụng API Gợi ý Âm nhạc

## Tổng quan

API gợi ý âm nhạc cho phép ứng dụng của bạn truy xuất danh sách bài hát được gợi ý dựa trên sở thích và thói quen nghe nhạc của người dùng. Hệ thống gợi ý sử dụng các yếu tố sau để tạo đề xuất cá nhân hóa:

1. **Bài hát yêu thích** - Đề xuất bài hát có cùng thể loại và nghệ sĩ với những bài hát yêu thích
2. **Lịch sử nghe** - Phân tích thói quen nghe nhạc gần đây của người dùng
3. **Đánh giá** - Đề xuất bài hát tương tự với những bài hát được đánh giá cao
4. **Lịch sử tìm kiếm** - Sử dụng từ khóa tìm kiếm gần đây để gợi ý bài hát liên quan

## API Endpoints

### Lấy gợi ý bài hát

```
GET /api/music/recommendations/songs/
```

#### Tham số truy vấn:

| Tham số | Kiểu    | Mô tả                              | Mặc định |
| ------- | ------- | ---------------------------------- | -------- |
| limit   | integer | Số lượng bài hát tối đa cần trả về | 10       |

#### Yêu cầu xác thực:

API này yêu cầu người dùng đăng nhập. Bạn cần cung cấp JWT token trong header:

```
Authorization: Bearer <your_token>
```

#### Phản hồi:

```json
{
  "results": [
    {
      "id": 123,
      "title": "Tên bài hát",
      "artist": "Tên nghệ sĩ",
      "album": "Tên album",
      "duration": 240,
      "audio_file": "https://example.com/path/to/audio.mp3",
      "cover_image": "https://example.com/path/to/cover.jpg",
      "genre": "Thể loại",
      "likes_count": 42,
      "play_count": 1024
    }
    // Các bài hát khác...
  ],
  "count": 10
}
```

#### Mã trạng thái:

- `200 OK` - Yêu cầu thành công
- `401 Unauthorized` - Người dùng chưa xác thực
- `500 Internal Server Error` - Lỗi máy chủ

## Command Line Tool

Hệ thống cũng cung cấp công cụ dòng lệnh để tạo đề xuất âm nhạc cho tất cả người dùng hoặc một người dùng cụ thể.

### Tạo đề xuất cho tất cả người dùng:

```bash
python manage.py generate_music_recommendations
```

### Tạo đề xuất cho một người dùng cụ thể:

```bash
python manage.py generate_music_recommendations --user-id=123
```

### Chỉ định số lượng đề xuất:

```bash
python manage.py generate_music_recommendations --limit=20
```

## Giải thích thuật toán

Thuật toán đề xuất âm nhạc hoạt động theo các bước sau:

1. **Thu thập dữ liệu người dùng**:

   - Lấy các thể loại yêu thích từ bài hát yêu thích và lịch sử nghe
   - Lấy danh sách nghệ sĩ yêu thích từ bài hát đã thích
   - Thu thập từ khóa tìm kiếm gần đây

2. **Loại trừ các bài hát đã biết**:

   - Loại bỏ bài hát đã nghe gần đây
   - Loại bỏ bài hát đã thích (người dùng đã biết về chúng)

3. **Ưu tiên theo thứ tự**:

   - Ưu tiên 1: Bài hát cùng thể loại với thể loại yêu thích
   - Ưu tiên 2: Bài hát cùng nghệ sĩ với nghệ sĩ yêu thích
   - Ưu tiên 3: Bài hát khớp với từ khóa tìm kiếm gần đây
   - Ưu tiên 4: Bài hát phổ biến (nếu không đủ kết quả từ các ưu tiên trên)

4. **Kết hợp kết quả**: Thuật toán kết hợp các kết quả từ nhiều nguồn để tạo danh sách đa dạng

## Ví dụ tích hợp

### JavaScript / Axios:

```javascript
import axios from "axios";

async function fetchRecommendations(token, limit = 10) {
  try {
    const response = await axios.get(
      "https://your-api.com/api/music/recommendations/songs/",
      {
        params: { limit },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data.results;
  } catch (error) {
    console.error("Error fetching recommendations:", error);
    return [];
  }
}
```

### Python / Requests:

```python
import requests

def get_recommendations(token, limit=10):
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        'https://your-api.com/api/music/recommendations/songs/',
        params={'limit': limit},
        headers=headers
    )

    if response.status_code == 200:
        return response.json()['results']
    else:
        print(f"Error: {response.status_code}")
        return []
```

## Hạn chế

- Hệ thống đề xuất hoạt động tốt nhất khi người dùng có lịch sử nghe và bài hát yêu thích
- Đối với người dùng mới hoặc ít hoạt động, hệ thống sẽ đề xuất bài hát phổ biến
- Đề xuất được tính toán theo thời gian thực và không được lưu trữ, có thể dẫn đến độ trễ cho các ứng dụng quy mô lớn
