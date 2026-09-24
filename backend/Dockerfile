FROM python:3.11-slim

# System deps for OpenCV, psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create media directory
RUN mkdir -p /app/media

EXPOSE 8000
