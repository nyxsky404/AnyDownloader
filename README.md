# Video Downloader API

## 🚀 Setup

### Prerequisites
- Python 3.11+
- FFmpeg installed on your system
- Node.js (for certain video platforms)

### Option 1: Local Setup

1. **Clone and navigate to project**
```bash
cd /path/to/project
```

2. **Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create `.env` file** (copy from below or use defaults)
```bash
LOCAL_DOWNLOAD_DIR=./downloads
API_HOST=0.0.0.0
API_PORT=8000
```

5. **Run the API**
```bash
python api.py
```

API will be available at: **http://localhost:8000**

### Option 2: Docker Setup

1. **Start the service**
```bash
docker-compose up -d
```

2. **Check logs**
```bash
docker-compose logs -f
```

3. **Stop the service**
```bash
docker-compose down
```

API will be available at: **http://localhost:8000**

## 📖 Usage

### 1. Download a Video
```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### 2. Retrieve Downloaded Video
```bash
curl -O http://localhost:8000/video/video_dQw4w9WgXcQ.mp4
```

### 3. Access Interactive API Docs
Open in browser: **http://localhost:8000/docs**

**Note**: Downloaded videos are saved in `./downloads` folder

## ⚙️ Configuration (Optional)

Default `.env` settings:
```bash
LOCAL_DOWNLOAD_DIR=./downloads
DOWNLOAD_TIMEOUT=300
YT_DLP_MAX_RETRIES=3
YT_DLP_MAX_FILESIZE=500
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
LOG_FILE=video_downloader.log
```