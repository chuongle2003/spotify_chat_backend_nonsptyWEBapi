#!/bin/bash

# Dừng khi gặp lỗi
set -e

echo "Bắt đầu quá trình deployment..."

# 1. Cài đặt các gói cần thiết
echo "Cài đặt các gói cần thiết..."
sudo apt update
sudo apt install -y python3-pip python3-dev python3-venv nginx postgresql postgresql-contrib supervisor redis-server

# 2. Tạo thư mục ứng dụng
echo "Tạo thư mục ứng dụng..."
APP_DIR=/home/ubuntu/spotify-chat-backend
mkdir -p $APP_DIR
cp -r . $APP_DIR

# 3. Tạo và kích hoạt môi trường ảo
echo "Cài đặt môi trường Python..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Cấu hình Environment
echo "Cấu hình environment..."
cat > .env << EOL
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
MEDIA_ROOT=$APP_DIR/media/

# JWT Settings
JWT_EXPIRATION_DELTA=7
EOL

# 5. Tạo database
echo "Cấu hình database..."
sudo -u postgres psql -c "CREATE DATABASE spotify_chat_db;" || echo "Database đã tồn tại"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '123456';" || echo "Đã thiết lập mật khẩu"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE spotify_chat_db TO postgres;" || echo "Đã cấp quyền"

# 6. Tạo thư mục cần thiết
echo "Tạo các thư mục cần thiết..."
mkdir -p $APP_DIR/media $APP_DIR/static $APP_DIR/logs

# 7. Chạy migrations và collectstatic
echo "Chạy migrations và collectstatic..."
python manage.py migrate
python manage.py collectstatic --noinput

# 8. Cấu hình Gunicorn
echo "Cấu hình Gunicorn..."
cat > $APP_DIR/gunicorn.conf.py << EOL
# Gunicorn configuration
bind = "127.0.0.1:8000"
workers = 3
timeout = 120
accesslog = "$APP_DIR/logs/gunicorn-access.log"
errorlog = "$APP_DIR/logs/gunicorn-error.log"
capture_output = True
loglevel = "info"
EOL

# 9. Cấu hình Supervisor
echo "Cấu hình Supervisor..."
cat > spotify-chat.conf << EOL
[program:spotify-chat]
command=$APP_DIR/venv/bin/gunicorn -c $APP_DIR/gunicorn.conf.py backend.wsgi:application
directory=$APP_DIR
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/supervisor-stdout.log
stderr_logfile=$APP_DIR/logs/supervisor-stderr.log
environment=PYTHONUNBUFFERED=1

[program:daphne]
command=$APP_DIR/venv/bin/daphne -b 127.0.0.1 -p 8001 backend.asgi:application
directory=$APP_DIR
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/daphne-stdout.log
stderr_logfile=$APP_DIR/logs/daphne-stderr.log
environment=PYTHONUNBUFFERED=1
EOL
sudo mv spotify-chat.conf /etc/supervisor/conf.d/

# 10. Cấu hình Nginx
echo "Cấu hình Nginx..."
cat > spotify-chat-nginx << EOL
server {
    listen 80;
    server_name ec2-172-31-12-202.compute.amazonaws.com;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }

    location /static/ {
        alias $APP_DIR/static/;
    }

    location /media/ {
        alias $APP_DIR/media/;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL
sudo mv spotify-chat-nginx /etc/nginx/sites-available/spotify-chat

# 11. Kích hoạt Nginx site
echo "Kích hoạt cấu hình Nginx..."
sudo ln -sf /etc/nginx/sites-available/spotify-chat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 12. Khởi động Supervisor
echo "Khởi động Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

echo "Deployment hoàn tất! Truy cập ứng dụng tại: http://ec2-172-31-12-202.compute.amazonaws.com" 