# 개발용 Dockerfile 
FROM python:3.12-slim

WORKDIR /app

# 개발에 필요한 빌드 도구 및 라이브러리 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 개발 편의를 위한 환경 변수
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]