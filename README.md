# FreeDownloader Ecosystem

A high-performance, multi-service video downloading platform supporting YouTube, Facebook, Instagram, TikTok, and more. Built with Flask, Redis, Celery, and Nginx.

## Architecture Overview

The system is composed of several microservices, each specialized in a platform or a specific part of the business logic. All services are optimized for high concurrency and bypass bot detection using browser impersonation and proxy rotation.

### Core Services & Ports

| Service | Port | Directory | Description |
| :--- | :--- | :--- | :--- |
| **YouTube Downloader** | `8004` | `yt_d/` | Primary YouTube extraction engine with Invidious/Piped fallbacks. |
| **Facebook Downloader** | `8001` | `fb_downloader/` | Facebook video downloader using Snapsave JS decoding. |
| **Instagram Downloader** | `8002` | `insta_d/` | Instagram downloader with TLS impersonation. |
| **TikTok Downloader** | `8003` | `tik_d/` | Watermark-free TikTok downloader via tikwm API. |
| **P Downloader** | `8009` | `p_d/` | Specialized extractor for adult content platforms. |
| **Free Store** | `8010` | `freeStore/` | Central software catalog and main landing page. |
| **Donate App** | `5007` | `donate_app/` | Microservice for handling donations and support. |
| **Legacy Landing** | `8008` | `free_d/` | Legacy web landing page. |
| **Admin Backend** | `5000` | `backend/` | Central analytics, user tracking, and dashboard. |
| **phpMyAdmin** | `8080` | N/A | Database management interface. |

## Infrastructure

- **Nginx**: Handles reverse proxying, SSL (Certbot), and edge rate-limiting (zones for API info, download, and status).
- **Redis**: 
    - `DB 0`: Shared caching and rate-limiting storage.
    - `DB 1`: Celery broker and result backend.
- **Celery**: Background workers for long-running download tasks.
- **MySQL**: Stores analytics, software catalog, and user session data.
- **phpMyAdmin**: Web-based interface for MySQL database management.

## Configuration (Environment Variables)

Create a `.env` file in the root directory. See `.env.example` for details.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DB_HOST` | `localhost` | MySQL Database Host |
| `DB_USER` | `root` | MySQL Database User |
| `DB_PASSWORD` | `""` | MySQL Database Password |
| `DB_NAME` | `downloader_analytics` | MySQL Database Name |
| `REDIS_URL` | `redis://localhost:6379/0` | Shared Redis Cache URL |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery Broker URL |
| `YOUTUBE_API_KEY` | `AIza...` | YouTube Data API v3 Key |
| `PROXY_LIST` | `""` | Comma-separated list of proxies |
| `GUNICORN_WORKERS` | `CPU * 2` | Number of Gunicorn worker processes |

## Setup & Deployment

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   # Ensure redis-server and mysql-server are installed
   ```

2. **Initialize Database**:
   ```bash
   python backend/utils/db.py
   ```

3. **Run Services (Development)**:
   Navigate to each service directory and run:
   ```bash
   python app.py
   ```

4. **Production (Gunicorn + Nginx)**:
   Use the provided Nginx configs in `nginx/` and run services via Gunicorn:
   ```bash
   gunicorn -c infra/gunicorn.conf.py app:app
   ```

## Anti-Bot Features

- **TLS Impersonation**: Uses `curl-cffi` to mimic real browser TLS fingerprints.
- **Proxy Rotation**: Built-in proxy pool with automatic bad-proxy detection and cooldown.
- **PO Token Support**: Injects Proof of Origin tokens for YouTube extraction.
- **User-Agent Pool**: Automatically rotates through modern browser headers.
