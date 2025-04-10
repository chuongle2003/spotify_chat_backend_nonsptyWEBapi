# Hướng dẫn deploy ứng dụng lên AWS EC2

## Các bước triển khai tự động

### 1. Chuẩn bị

- Đã tạo EC2 instance (Ubuntu Server)
- Đã mở port 22 (SSH), 80 (HTTP), 443 (HTTPS) trong Security Group
- Đã có key pair để SSH

### 2. Đưa code lên EC2

```bash
# Option 1: Sử dụng scp để đưa toàn bộ code lên
scp -i Chuongle.2003.pem -r /path/to/your/project ubuntu@ec2-172-31-12-202.compute.amazonaws.com:~/

# Option 2: Hoặc sử dụng git clone trên server (nếu repo là public)
ssh -i Chuongle.2003.pem ubuntu@ec2-172-31-12-202.compute.amazonaws.com
git clone https://github.com/your-username/spotify-chat-backend.git
```

### 3. Triển khai sử dụng script

```bash
# Kết nối SSH vào EC2
ssh -i Chuongle.2003.pem ubuntu@ec2-172-31-12-202.compute.amazonaws.com

# Chuyển vào thư mục project
cd spotify-chat-backend

# Cấp quyền thực thi cho script
chmod +x deploy.sh

# Chạy script deploy
./deploy.sh
```

### 4. Kiểm tra và xử lý lỗi (nếu có)

```bash
# Kiểm tra logs Nginx
sudo tail -f /var/log/nginx/error.log

# Kiểm tra logs của ứng dụng
tail -f ~/spotify-chat-backend/logs/supervisor-stderr.log
tail -f ~/spotify-chat-backend/logs/daphne-stderr.log
tail -f ~/spotify-chat-backend/logs/gunicorn-error.log

# Kiểm tra trạng thái của các services
sudo systemctl status nginx
sudo supervisorctl status
```

## Các bước triển khai thủ công

Nếu bạn muốn triển khai thủ công thay vì sử dụng script tự động, hãy làm theo các bước sau:

### 1. Cài đặt các gói cần thiết

```bash
sudo apt update
sudo apt install -y python3-pip python3-dev python3-venv nginx postgresql postgresql-contrib supervisor
```

### 2. Cài đặt và cấu hình PostgreSQL

```bash
# Tạo database
sudo -u postgres psql -c "CREATE DATABASE spotify_chat_db;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '123456';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE spotify_chat_db TO postgres;"
```

### 3. Cài đặt môi trường Python

```bash
# Tạo thư mục và clone code
mkdir -p ~/spotify-chat-backend
cd ~/spotify-chat-backend

# Tạo và kích hoạt môi trường ảo
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Cấu hình các file settings

Tạo file `.env` với nội dung:

```
# Django Configuration
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=ec2-172-31-12-202.compute.amazonaws.com,localhost,127.0.0.1

# Database Configuration
DB_NAME=spotify_chat_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=5432

# Media Storage
MEDIA_URL=/media/
MEDIA_ROOT=/home/ubuntu/spotify-chat-backend/media/

# JWT Settings
JWT_EXPIRATION_DELTA=7
```

### 5. Cấu hình Nginx

Tạo file cấu hình:

```bash
sudo nano /etc/nginx/sites-available/spotify-chat
```

Thêm nội dung:

```nginx
server {
    listen 80;
    server_name ec2-172-31-12-202.compute.amazonaws.com;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        alias /home/ubuntu/spotify-chat-backend/static/;
    }

    location /media/ {
        alias /home/ubuntu/spotify-chat-backend/media/;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. Cấu hình Supervisor

Tạo file cấu hình:

```bash
sudo nano /etc/supervisor/conf.d/spotify-chat.conf
```

Thêm nội dung:

```ini
[program:spotify-chat]
command=/home/ubuntu/spotify-chat-backend/venv/bin/gunicorn backend.wsgi:application -b 127.0.0.1:8000
directory=/home/ubuntu/spotify-chat-backend
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ubuntu/spotify-chat-backend/logs/supervisor-stdout.log
stderr_logfile=/home/ubuntu/spotify-chat-backend/logs/supervisor-stderr.log
environment=PYTHONUNBUFFERED=1

[program:daphne]
command=/home/ubuntu/spotify-chat-backend/venv/bin/daphne -b 127.0.0.1 -p 8001 backend.asgi:application
directory=/home/ubuntu/spotify-chat-backend
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ubuntu/spotify-chat-backend/logs/daphne-stdout.log
stderr_logfile=/home/ubuntu/spotify-chat-backend/logs/daphne-stderr.log
environment=PYTHONUNBUFFERED=1
```

### 7. Kích hoạt và khởi động các dịch vụ

```bash
# Kích hoạt cấu hình Nginx
sudo ln -sf /etc/nginx/sites-available/spotify-chat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Khởi động Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all
```

## Các lưu ý quan trọng

1. **Security Groups**: Đảm bảo đã mở port 80 (HTTP), 22 (SSH) và các port khác cần thiết
2. **Database**: Sử dụng mật khẩu mạnh cho database trong môi trường production
3. **HTTPS**: Nếu cần HTTPS, hãy cài đặt Let's Encrypt và cấu hình SSL
4. **Backup**: Thiết lập backup định kỳ cho database và media files
5. **Monitoring**: Cân nhắc sử dụng công cụ monitoring như New Relic hoặc Prometheus

## Kiểm tra triển khai

Sau khi triển khai, truy cập API tại:

```
http://ec2-172-31-12-202.compute.amazonaws.com
```

## Xử lý sự cố

1. **Lỗi 502 Bad Gateway**: Kiểm tra logs của Gunicorn và Daphne, đảm bảo các service đang chạy
2. **Lỗi Static Files**: Kiểm tra đường dẫn trong Nginx và chạy lại `collectstatic`
3. **Lỗi Database**: Kiểm tra thông tin kết nối database trong file `.env`
