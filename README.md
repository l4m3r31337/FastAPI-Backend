# Async Currency Backend

## Запуск проекта

### 1. Установить зависимости
pip install -r requirements.txt

### 2. Запустить NATS
docker run -p 4222:4222 nats

### 3. Запустить сервер
uvicorn app.main:app --reload

## Документация API
http://127.0.0.1:8000/docs
