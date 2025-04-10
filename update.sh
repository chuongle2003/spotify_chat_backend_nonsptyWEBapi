#!/bin/bash

set -e  # Dừng nếu có lỗi

echo "🔄 Bắt đầu quá trình cập nhật ứng dụng..."

APP_DIR=/home/ubuntu/spotify_chat_backend_nonsptyWEBapi

# 1. Vào thư mục project
cd $APP_DIR

# 2. Pull code mới nhất từ GitHub
echo "📥 Đang pull code mới từ GitHub..."
git pull origin main

# 3. Kích hoạt môi trường ảo
echo "🐍 Kích hoạt môi trường Python..."
if [ ! -d "venv" ]; then
    echo "⚠️ Môi trường ảo chưa có, đang tạo..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 4. Cài thêm packages mới (nếu có)
echo "📦 Cài thêm dependencies (nếu có)..."
pip install -r requirements.txt

# 5. Chạy migrate
echo "🛠️ Chạy migrate..."
python manage.py migrate

# 6. Collect static files
echo "🎨 Collect static files..."
python manage.py collectstatic --noinput

# 7. Restart app với Supervisor
echo "🔁 Khởi động lại Supervisor..."
sudo supervisorctl restart all

echo "✅ Cập nhật hoàn tất! App đã được làm mới ✨"
