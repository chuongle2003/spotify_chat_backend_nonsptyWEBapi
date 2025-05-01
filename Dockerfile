   FROM python:3.12-slim

   WORKDIR /app

   RUN apt-get update && apt-get install -y \
       gcc \
       libpq-dev \
       python3-dev \
       build-essential \
       libssl-dev \
       ffmpeg \
       && rm -rf /var/lib/apt/lists/*

   COPY requirements.txt .

   RUN pip install --upgrade pip && pip install -r requirements.txt

   COPY . .

   # Tạo thư mục để lưu trữ media files
   RUN mkdir -p /app/media/songs /app/media/images /app/media/albums

   # Cài đặt quyền
   RUN chmod -R 755 /app/media

   CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers=4 --timeout=120"]
