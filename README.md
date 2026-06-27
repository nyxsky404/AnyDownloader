# Any Downloader — Free Video Downloader for YouTube, Instagram, TikTok, Twitter/X, Facebook & 1000+ Sites

**Any Downloader** is a free, open-source video downloader that lets you save videos from YouTube, Instagram, TikTok, Twitter/X, Facebook, Reddit, Twitch, Vimeo, Dailymotion, Pinterest, LinkedIn, and [1000+ other websites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). It ships a clean web UI (Streamlit) and a REST API — self-host it in minutes with Docker or deploy to the cloud for free on Render.

> Paste any video URL → preview in browser → download as MP4. No ads, no limits, no account required.

## Supported Platforms

| Platform | Videos | Shorts / Reels | Playlists | Live |
|----------|--------|----------------|-----------|------|
| **YouTube** | ✅ | ✅ Shorts | ✅ | ✅ |
| **Instagram** | ✅ | ✅ Reels | ✅ | — |
| **TikTok** | ✅ | ✅ | ✅ | — |
| **Twitter / X** | ✅ | — | — | — |
| **Facebook** | ✅ | ✅ Reels | ✅ | ✅ |
| **Reddit** | ✅ | — | — | — |
| **Twitch** | ✅ Clips | — | ✅ VODs | ✅ |
| **Vimeo** | ✅ | — | ✅ | — |
| **Dailymotion** | ✅ | — | ✅ | — |
| **Pinterest** | ✅ | — | — | — |
| **LinkedIn** | ✅ | — | — | — |
| **SoundCloud** | ✅ Audio | — | ✅ | — |
| **1000+ more** | [Full list →](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) | | | |

## Services

| Service | URL | Description |
|---------|-----|-------------|
| **Streamlit UI** | http://localhost:8501 | Paste a URL, preview the video, download it |
| **FastAPI backend** | http://localhost:8000 | REST API for programmatic use |
| **API docs** | http://localhost:8000/docs | Interactive Swagger UI |

## ☁️ Render Deployment

A single Docker service runs both the API and Streamlit UI in one container. The included `render.yaml` configures everything automatically.

### Steps

1. **Push your repo to GitHub** (already done)

2. **Deploy via Render Blueprint**
   - Go to [render.com](https://render.com) → **New** → **Blueprint**
   - Connect your GitHub repo — Render will detect `render.yaml` and create the service

3. **Set environment variable on the service**
   - `YT_DLP_COOKIES_CONTENT` — paste the full contents of your `cookies.txt` (for YouTube downloads)

4. Open the **service URL** — Render routes external traffic to the Streamlit UI (port 8501)

> **Note:** Render free tier services spin down after inactivity. The first request may take ~30 seconds to wake up.

---

## 🐳 Docker (Local)

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
- Node.js 22+ (for JS-heavy platforms like TikTok, Instagram)

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
├── docker-compose.yml   # Spins up API + UI locally
├── render.yaml          # Render single-service deployment config
├── requirements.txt
├── cookies.txt          # YouTube cookies (gitignored)
└── downloads/           # Downloaded videos (gitignored)
```

---

## ❓ FAQ

**Can I download YouTube videos for free?**
Yes. Any Downloader is free and open-source. Self-host it locally or deploy to Render's free tier.

**Which video formats are supported?**
Downloads are saved as MP4 (up to 4K / 2160p where available). Audio-only platforms like SoundCloud are saved as MP3/M4A.

**Can I download YouTube playlists?**
Yes — paste the playlist URL and every video in the playlist downloads automatically, each with its own preview and save button.

**Why does YouTube download fail without cookies?**
YouTube's bot-detection blocks anonymous yt-dlp requests. Adding a `cookies.txt` file from a logged-in session bypasses this. See [YouTube Cookies](#-youtube-cookies).

**Can I download private or age-restricted videos?**
If you are logged into the account that has access and export those cookies, yes.

**Is this an alternative to youtube-dl?**
Any Downloader is built on [yt-dlp](https://github.com/yt-dlp/yt-dlp), the actively maintained fork of youtube-dl with significantly faster downloads, more sites, and better format selection.

**Can I use this as a video downloader API?**
Yes — the FastAPI backend exposes a `/download` endpoint you can call from any language. See [API Usage](#-api-usage).

**What is the maximum file size?**
500 MB by default. Change `YT_DLP_MAX_FILESIZE` in your `.env` to raise or remove the limit.

**Does it work on Windows / Mac / Linux?**
Yes — run it natively with Python or via Docker on any OS.

---

## 🏷️ Keywords

`video downloader` · `youtube downloader` · `instagram video downloader` · `tiktok downloader` · `twitter video downloader` · `facebook video downloader` · `reddit video downloader` · `twitch clip downloader` · `vimeo downloader` · `yt-dlp web ui` · `yt-dlp gui` · `self-hosted video downloader` · `open source video downloader` · `download youtube playlist` · `python video downloader` · `fastapi yt-dlp`