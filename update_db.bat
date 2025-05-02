@echo off
REM Thiết lập biến môi trường
set DB_HOST=localhost
set DB_NAME=spotify_chat_db
set DB_USER=postgres
set DB_PASSWORD=123456
set DB_PORT=5432

echo === Makemigrations - Tạo các tệp migration ===
python manage.py makemigrations

echo === Migrate - Cập nhật cơ sở dữ liệu ===
python manage.py migrate

echo === Hoàn tất ===
pause 