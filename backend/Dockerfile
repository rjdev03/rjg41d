FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY data/raw/windfor-2026-01.json /data/raw/windfor-2026-01.json
COPY data/raw/fuelhh-wind-2026-01.json /data/raw/fuelhh-wind-2026-01.json

ENV DATA_DIR=/data/raw

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
