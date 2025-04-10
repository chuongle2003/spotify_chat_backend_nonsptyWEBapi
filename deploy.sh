#!/bin/bash

# Dừng khi có lỗi
set -e

echo "🚀 Bắt đầu quá trình deployment..."

# 1. Cài đặt các gói cần thiết
echo "📦 Cài đặt dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-dev python3-venv nginx postgresql postgresql-contrib supervisor redis-server

# 2. Tạo thư mục ứng dụng
APP_DIR=/home/ubuntu/spotify-chat-backend
echo "📁 Tạo thư mục ứng dụng tại $APP_DIR..."
mkdir -p $APP_DIR
cp -r . $APP_DIR

# 3. Thiết lập môi trường Python
echo "🐍 Tạo môi trường ảo và cài dependencies..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install django-environ

# 4. Cấu hình .env
echo "⚙️ Cấu hình environment (.env)..."
cat > .env << EOF
# Django Configuration
SECRET_KEY=tIkg6sBSU6ICcUO9LCoK1ET-9s3TZBM6wkCNKWEpJGy4bfm-1ocGd1fkaNxfcnjnugU
DEBUG=False
ALLOWED_HOSTS=3.27.160.138,localhost,127.0.0.1

# Database Configuration
DB_NAME=spotify_chat_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=5432

# Media Storage
MEDIA_URL=/media/
MEDIA_ROOT=$APP_DIR/media/
EOF

# 5. Cấu hình PostgreSQL
echo "🗃️ Cấu hình PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE spotify_chat_db;" || echo "⚠️ Database đã tồn tại"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '123456';" || echo "⚠️ Đã thiết lập mật khẩu"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE spotify_chat_db TO postgres;" || echo "⚠️ Đã cấp quyền"

# 6. Tạo các thư mục cần thiết
echo "📂 Tạo thư mục static, media, logs..."
mkdir -p $APP_DIR/media $APP_DIR/static $APP_DIR/logs

# 7. Migrate & Collect Static
echo "⚙️ Migrate và collectstatic..."
python manage.py migrate
python manage.py collectstatic --noinput

# 8. Gunicorn config
echo "📝 Tạo cấu hình Gunicorn..."
cat > $APP_DIR/gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 3
timeout = 120
accesslog = "$APP_DIR/logs/gunicorn-access.log"
errorlog = "$APP_DIR/logs/gunicorn-error.log"
capture_output = True
loglevel = "info"
EOF

# 9. Supervisor config
echo "🧩 Cấu hình Supervisor..."
cat > spotify-chat.conf << EOF
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
EOF
sudo mv spotify-chat.conf /etc/supervisor/conf.d/

# 10. Nginx config
echo "🌐 Tạo cấu hình Nginx..."
cat > spotify-chat-nginx << EOF
server {
    listen 80 default_server;
    server_name 3.27.160.138;

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
EOF
sudo mv spotify-chat-nginx /etc/nginx/sites-available/spotify-chat
sudo ln -sf /etc/nginx/sites-available/spotify-chat /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 11. Reload Nginx
echo "🔁 Restart Nginx..."
sudo nginx -t
sudo systemctl restart nginx

# 12. Restart Supervisor
echo "🔁 Khởi động lại Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

echo "✅ Deployment hoàn tất! Truy cập tại: http://3.27.160.138"
