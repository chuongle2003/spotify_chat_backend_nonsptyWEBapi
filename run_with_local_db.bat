@echo off
REM Thiết lập biến môi trường tạm thời
set DB_HOST=localhost
set DB_NAME=spotify_chat_db
set DB_USER=postgres
set DB_PASSWORD=123456
set DB_PORT=5432

REM Chạy lệnh Django
echo === Tạo dữ liệu mẫu ===
python manage.py generate_data --force

pause 