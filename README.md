# Any Downloader

Download videos from any platform — YouTube, YouTube Shorts, Twitter/X, Facebook, Instagram, TikTok, and [thousands more](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) supported by yt-dlp.

## Services

| Service | URL | Description |
|---------|-----|-------------|
| **Streamlit UI** | http://localhost:8501 | Paste a URL, preview the video, download it |
| **FastAPI backend** | http://localhost:8000 | REST API for programmatic use |
| **API docs** | http://localhost:8000/docs | Interactive Swagger UI |

## 🚀 Quick Start (Docker — recommended)

1. **Create a `cookies.txt` file** (required before Docker mounts it)
```bash
touch cookies.txt
```
> For YouTube downloads, populate this file with real cookies — see [YouTube Cookies](#-youtube-cookies) below.

2. **Start both services**
```bash
docker-compose up -d
```

3. **Open the UI**

Navigate to **http://localhost:8501**, paste any video URL, and hit **Download**.

4. **Stop**
```bash
docker-compose down
```

---

## 🖥️ Streamlit UI

The UI communicates with the FastAPI backend internally. Here's the flow:

1. Paste any video URL into the input box
2. Click **⬇️ Download** — the backend fetches and saves the video via yt-dlp
3. An **inline video preview** appears once the download completes
4. Click **💾 Save** to download the file to your machine
5. For playlists, each video gets its own collapsible card with preview + save button

---

## 🚀 Local Setup (without Docker)

### Prerequisites
- Python 3.11+
- FFmpeg (`brew install ffmpeg` / `apt install ffmpeg`)
- Node.js 20+ (for JS-heavy platforms)

```bash
# 1. Create and activate virtualenv
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env  # or create .env manually

# 4. Start the API
python api.py

# 5. Start the UI (separate terminal)
streamlit run streamlit_app.py
```

---

## 🍪 YouTube Cookies

YouTube requires authentication to avoid bot detection. Other platforms generally work without cookies.

### Method 1: Browser Extension + Incognito (Recommended)

**Install:**
- [Chrome — Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- [Firefox — cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

**Export (prevents cookie rotation):**
1. Open a **new incognito/private window**
2. Log into YouTube with a **dedicated throwaway account**
3. Navigate to `https://www.youtube.com/robots.txt`
4. Export cookies → save as `cookies.txt` in the project root
5. **Close the incognito window immediately** — never reopen it

### Method 2: yt-dlp Built-in

```bash
# Chrome
yt-dlp --cookies-from-browser chrome "https://youtube.com" --print-to-file "%(cookies)s" cookies.txt

# Firefox
yt-dlp --cookies-from-browser firefox "https://youtube.com" --print-to-file "%(cookies)s" cookies.txt
```

### ⚠️ Notes

- Use a **dedicated Google account**, not your personal one
- Cookies last **3–6 months** — refresh when YouTube downloads start failing
- Monitor status: `curl http://localhost:8000/cookies/status`
- Rate limits: ~300/hr without cookies, ~2000/hr with

---

## 📖 API Usage

### Download a video
```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Retrieve a downloaded file
```bash
curl -O http://localhost:8000/video/video_dQw4w9WgXcQ.mp4
```

### Health check
```bash
curl http://localhost:8000/health
```

### Cookie status
```bash
curl http://localhost:8000/cookies/status
```

---

## ⚙️ Configuration

`.env` defaults:
```bash
LOCAL_DOWNLOAD_DIR=./downloads
DOWNLOAD_TIMEOUT=300
YT_DLP_MAX_RETRIES=3
YT_DLP_MAX_FILESIZE=500        # MB
YT_DLP_COOKIES_FILE=./cookies.txt
YT_DLP_COOKIES_CONTENT=        # Optional: paste cookie content directly (for cloud deploys)
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
LOG_FILE=video_downloader.log
```

---

## 📁 File Structure

```
├── api.py               # FastAPI endpoints
├── streamlit_app.py     # Streamlit UI
├── downloader.py        # yt-dlp download logic
├── models.py            # Pydantic request/response models
├── cookies_checker.py   # Cookie validation
├── config.py            # Settings
├── Dockerfile
├── docker-compose.yml   # Spins up API + UI
├── requirements.txt
├── cookies.txt          # YouTube cookies (gitignored)
└── downloads/           # Downloaded videos (gitignored)
```