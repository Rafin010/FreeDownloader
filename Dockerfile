# Use a modern Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    npm \
    curl \
    g++ \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all requirements files first to leverage Docker cache
# We find all requirements.txt files and merge them for a single install
COPY ./yt_d/requirements.txt ./yt_d_req.txt
COPY ./fb_downloader/requirements.txt ./fb_req.txt
COPY ./insta_d/requirements.txt ./insta_req.txt
COPY ./tik_d/requirements.txt ./tik_req.txt
COPY ./p_d/requirements.txt ./p_req.txt
COPY ./backend/requirements.txt ./backend_req.txt

# Merge and install Python dependencies
RUN cat *_req.txt | sort | uniq > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn gevent curl-cffi \
    && rm *_req.txt requirements.txt

# Copy the entire project
COPY . .

# Ensure downloads/uploads directories exist with correct permissions
RUN mkdir -p yt_d/downloads fb_downloader/downloads insta_d/downloads \
    tik_d/downloads p_d/downloads freeStore/uploads \
    && chmod -R 777 yt_d/downloads fb_downloader/downloads insta_d/downloads \
    tik_d/downloads p_d/downloads freeStore/uploads

# The actual command is overridden in docker-compose.yml
CMD ["python", "backend/app.py"]
