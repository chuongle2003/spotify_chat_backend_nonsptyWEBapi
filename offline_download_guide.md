# Hướng dẫn triển khai chức năng tải nhạc nghe offline

## Giới thiệu

Chức năng tải nhạc nghe offline cho phép người dùng tải bài hát về thiết bị và nghe nhạc ngay cả khi không có kết nối internet. Tài liệu này hướng dẫn cách tích hợp và sử dụng API offline download trong ứng dụng front-end.

## API Endpoints

### 1. Danh sách bài hát đã tải xuống

**Endpoint:** `GET /api/offline/downloads/`

**Response:**

```json
[
  {
    "id": 1,
    "song_details": {
      "id": 25,
      "title": "Hello",
      "artist": "Adele",
      "duration": 295,
      "audio_file": "http://example.com/media/songs/hello.mp3",
      "cover_image": "http://example.com/media/covers/hello.jpg"
    },
    "status": "COMPLETED",
    "status_display": "Đã tải xuống hoàn tất",
    "progress": 100,
    "download_time": "2023-10-15T14:30:00Z",
    "expiry_time": "2023-11-14T14:30:00Z",
    "is_active": true,
    "is_available": true
  }
]
```

### 2. Yêu cầu tải xuống bài hát

**Endpoint:** `POST /api/offline/download/`

**Request Body:**

```json
{
  "song_id": 42
}
```

**Response:**

```json
{
  "message": "Đã thêm vào hàng đợi tải xuống",
  "download": {
    "id": 2,
    "song_details": {
      "id": 42,
      "title": "Rolling in the Deep",
      "artist": "Adele"
    },
    "status": "PENDING",
    "status_display": "Đang chờ tải xuống",
    "progress": 0
  }
}
```

### 3. Kiểm tra trạng thái tải xuống

**Endpoint:** `GET /api/offline/downloads/{download_id}/`

**Response:**

```json
{
  "id": 2,
  "song_details": {
    "id": 42,
    "title": "Rolling in the Deep",
    "artist": "Adele"
  },
  "status": "DOWNLOADING",
  "status_display": "Đang tải xuống",
  "progress": 45,
  "download_time": "2023-10-15T15:00:00Z"
}
```

### 4. Xóa bài hát đã tải xuống

**Endpoint:** `DELETE /api/offline/downloads/{download_id}/delete/`

**Response:**

```json
{
  "message": "Đã xóa bài hát khỏi danh sách tải xuống offline"
}
```

## Luồng hoạt động của chức năng

1. **Hiển thị danh sách bài hát đã tải xuống**

   - Gọi API `GET /api/offline/downloads/`
   - Hiển thị danh sách với trạng thái của từng bài hát
   - Đối với những bài hát đã tải hoàn tất (`status: COMPLETED`), hiển thị nút phát và cho phép người dùng nghe ngay cả khi offline

2. **Tải xuống bài hát mới**

   - Hiển thị nút "Tải xuống" bên cạnh mỗi bài hát trong danh sách phát/tìm kiếm
   - Khi người dùng nhấn nút, gọi API `POST /api/offline/download/` với `song_id` tương ứng
   - Hiển thị thông báo xác nhận khi bài hát được thêm vào hàng đợi tải xuống

3. **Theo dõi tiến trình tải xuống**

   - Sau khi bắt đầu tải xuống, cập nhật tiến trình thường xuyên bằng cách gọi API `GET /api/offline/downloads/{download_id}/`
   - Hiển thị thanh tiến trình cho người dùng

4. **Xóa bài hát offline**
   - Hiển thị nút "Xóa" bên cạnh mỗi bài hát đã tải xuống
   - Khi người dùng nhấn nút, hiển thị hộp thoại xác nhận
   - Sau khi xác nhận, gọi API `DELETE /api/offline/downloads/{download_id}/delete/`
   - Cập nhật lại danh sách bài hát đã tải xuống

## Các trạng thái của bài hát tải xuống

| Trạng thái  | Mô tả                 |
| ----------- | --------------------- |
| PENDING     | Đang chờ tải xuống    |
| DOWNLOADING | Đang tải xuống        |
| COMPLETED   | Đã tải xuống hoàn tất |
| FAILED      | Tải xuống thất bại    |
| EXPIRED     | Đã hết hạn            |

## Tích hợp vào giao diện người dùng

### 1. Thêm tab "Offline" trong thư viện nhạc

Thêm một tab mới trong phần Thư viện nhạc để hiển thị các bài hát đã tải xuống:

```jsx
function OfflineTab() {
  const [offlineDownloads, setOfflineDownloads] = useState([]);

  useEffect(() => {
    // Fetch offline downloads when component mounts
    fetchOfflineDownloads();
  }, []);

  const fetchOfflineDownloads = async () => {
    try {
      const response = await api.get("/offline/downloads/");
      setOfflineDownloads(response.data);
    } catch (error) {
      console.error("Error fetching offline downloads:", error);
    }
  };

  return (
    <div className="offline-tab">
      <h2>Bài hát offline</h2>
      <div className="offline-songs-list">
        {offlineDownloads.map((download) => (
          <OfflineSongItem
            key={download.id}
            download={download}
            onDelete={() => handleDelete(download.id)}
          />
        ))}
      </div>
    </div>
  );
}
```

### 2. Thêm nút tải xuống trong trang chi tiết bài hát

```jsx
function SongDetailPage({ song }) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadStatus, setDownloadStatus] = useState(null);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const response = await api.post("/offline/download/", {
        song_id: song.id,
      });
      setDownloadStatus(response.data.download);

      // Bắt đầu theo dõi tiến trình tải xuống nếu cần
      if (
        response.data.download.status === "PENDING" ||
        response.data.download.status === "DOWNLOADING"
      ) {
        startDownloadTracking(response.data.download.id);
      }
    } catch (error) {
      console.error("Error downloading song:", error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="song-detail">
      <h1>{song.title}</h1>
      <p>Artist: {song.artist}</p>

      {/* Nút tải xuống */}
      <button
        onClick={handleDownload}
        disabled={isDownloading}
        className="download-button"
      >
        {isDownloading ? "Đang xử lý..." : "Tải xuống để nghe offline"}
      </button>

      {downloadStatus && (
        <div className="download-status">
          <p>Trạng thái: {downloadStatus.status_display}</p>
          {downloadStatus.status === "DOWNLOADING" && (
            <ProgressBar progress={downloadStatus.progress} />
          )}
        </div>
      )}
    </div>
  );
}
```

### 3. Hiển thị biểu tượng bài hát có sẵn offline

Khi hiển thị danh sách bài hát, cần kiểm tra những bài hát đã được tải xuống để hiển thị biểu tượng phù hợp:

```jsx
function SongsList({ songs }) {
  const [offlineDownloads, setOfflineDownloads] = useState({});

  useEffect(() => {
    // Fetch offline downloads when component mounts
    fetchOfflineDownloads();
  }, []);

  const fetchOfflineDownloads = async () => {
    try {
      const response = await api.get("/offline/downloads/");

      // Chuyển đổi mảng thành object để dễ kiểm tra
      const downloadsMap = {};
      response.data.forEach((download) => {
        downloadsMap[download.song_details.id] = download;
      });

      setOfflineDownloads(downloadsMap);
    } catch (error) {
      console.error("Error fetching offline downloads:", error);
    }
  };

  return (
    <div className="songs-list">
      {songs.map((song) => (
        <div key={song.id} className="song-item">
          <span className="song-title">{song.title}</span>

          {/* Hiển thị icon nếu bài hát đã tải offline */}
          {offlineDownloads[song.id] &&
            offlineDownloads[song.id].status === "COMPLETED" && (
              <span className="offline-icon" title="Bài hát có sẵn offline">
                <i className="fa fa-download"></i>
              </span>
            )}
        </div>
      ))}
    </div>
  );
}
```

## Đảm bảo dữ liệu offline

Để đảm bảo người dùng có thể nghe nhạc khi offline, front-end cần:

1. **Lưu danh sách bài hát offline vào trình duyệt**

   - Sử dụng IndexedDB hoặc localStorage để lưu danh sách bài hát đã tải xuống
   - Lưu các bài hát đã tải xuống vào bộ nhớ cục bộ (nếu là ứng dụng di động)

2. **Phát nhạc từ bộ nhớ cục bộ**

   - Khi người dùng chọn phát bài hát đã tải xuống, sử dụng đường dẫn local thay vì URL từ server
   - Đối với web, có thể sử dụng URL object được tạo từ Blob lưu trữ

3. **Kiểm tra và xử lý hết hạn**
   - Kiểm tra trường `expiry_time` của mỗi bài hát offline
   - Hiển thị cảnh báo cho người dùng khi bài hát sắp hết hạn
   - Tự động xóa bài hát đã hết hạn để tiết kiệm không gian lưu trữ

## Lưu ý triển khai

1. **Khả năng tương thích:**

   - Web: Tính năng tải xuống hoạt động tốt nhất trên các trình duyệt hỗ trợ File System Access API hoặc IndexedDB
   - Mobile: Tính năng tải xuống yêu cầu quyền truy cập bộ nhớ thiết bị

2. **Quản lý bộ nhớ:**

   - Hiển thị dung lượng bộ nhớ đã sử dụng cho tính năng offline
   - Cho phép người dùng giới hạn không gian lưu trữ tối đa

3. **Người dùng không đăng nhập:**

   - Tính năng offline chỉ khả dụng cho người dùng đã đăng nhập
   - Hiển thị thông báo yêu cầu đăng nhập khi người dùng cố gắng tải xuống bài hát

4. **Đồng bộ hóa giữa các thiết bị:**
   - Khi người dùng đăng nhập trên thiết bị mới, hiển thị danh sách bài hát đã tải xuống trên các thiết bị khác
   - Cho phép người dùng chọn tải xuống lại những bài hát đó

---

Với hướng dẫn trên, bạn có thể triển khai đầy đủ tính năng tải xuống và nghe nhạc offline vào ứng dụng front-end.
