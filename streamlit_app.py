import json
import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Any Downloader",
    page_icon="🎬",
    layout="centered",
)

st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .stVideo { border-radius: 12px; overflow: hidden; }
        .stDownloadButton > button {
            width: 100%;
            background-color: #FF4B4B;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem 1rem;
        }
        .stDownloadButton > button:hover { background-color: #e03e3e; }
        .video-card {
            background: #1e1e2e;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 Any Downloader")
st.caption("Paste any video URL — YouTube, Twitter/X, Facebook, Instagram, TikTok, and more.")

url = st.text_input(
    "Video URL",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)

col1, col2 = st.columns([3, 1])
with col2:
    download_clicked = st.button("⬇️ Download", use_container_width=True, type="primary")


def fetch_video_bytes(download_url: str) -> bytes | None:
    """Fetch video bytes from the API server."""
    try:
        full_url = f"{API_BASE_URL}{download_url}"
        resp = requests.get(full_url, timeout=120, stream=True)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


def render_video_card(title: str, filename: str, download_url: str, index: int = 0):
    """Render a single video with preview and download button."""
    st.markdown(f"**{title or filename}**")

    video_bytes = fetch_video_bytes(download_url)

    if video_bytes:
        st.video(video_bytes)
        st.download_button(
            label=f"💾 Save  {filename}",
            data=video_bytes,
            file_name=filename,
            mime="video/mp4",
            key=f"dl_{index}_{filename}",
            use_container_width=True,
        )
    else:
        st.warning("Preview unavailable. Try the direct link below.")
        st.code(f"{API_BASE_URL}{download_url}")


def render_result(data: dict):
    video_type = data.get("type")
    if video_type == "playlist":
        playlist_title = data.get("playlist_title", "Playlist")
        filenames = data.get("filenames", [])
        download_urls = data.get("download_urls", [])
        count = data.get("video_count", 0)

        st.success(f"Playlist downloaded — {count} video(s)")
        st.subheader(f"📂 {playlist_title} — {count} video(s)")

        for i, (fname, dl_url) in enumerate(zip(filenames, download_urls)):
            with st.expander(f"Video {i + 1}: {fname}", expanded=(i == 0)):
                render_video_card(title=fname, filename=fname, download_url=dl_url, index=i)
    else:
        title = data.get("video_title", "")
        filename = data.get("filename", "video.mp4")
        dl_url = data.get("download_url", "")
        platform = data.get("platform", "")

        st.success("Video downloaded successfully")
        if platform:
            st.caption(f"Platform: `{platform}`")
        render_video_card(title=title, filename=filename, download_url=dl_url, index=0)


if download_clicked:
    if not url.strip():
        st.error("Please enter a video URL.")
    else:
        log_placeholder = st.empty()
        logs: list[str] = []
        result_data = None
        error_msg = None

        try:
            with st.spinner("Downloading… this may take a moment"), requests.post(
                f"{API_BASE_URL}/download/stream",
                json={"url": url.strip()},
                stream=True,
                timeout=600,
            ) as resp:
                if resp.status_code != 200:
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except Exception:
                        detail = resp.text
                    if resp.status_code == 422:
                        st.error(f"Validation error: {detail}")
                    else:
                        st.error(f"Download failed ({resp.status_code}): {detail}")
                else:
                    for raw_line in resp.iter_lines():
                        if not raw_line:
                            continue
                        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                        if not line.startswith("data: "):
                            continue
                        event = json.loads(line[6:])

                        if event["type"] == "log":
                            logs.append(event["message"])
                            log_placeholder.code("\n".join(logs), language=None)
                        elif event["type"] == "result":
                            result_data = event["data"]
                        elif event["type"] == "error":
                            error_msg = event["message"]

        except requests.exceptions.ConnectionError:
            st.error(f"Cannot reach the API at `{API_BASE_URL}`. Make sure the backend is running.")
        except requests.exceptions.Timeout:
            st.error("Request timed out. The video may be very large — try again.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

        if error_msg:
            st.error(f"Download failed: {error_msg}")
        elif result_data:
            render_result(result_data)

st.divider()
with st.expander("⚙️ API Status"):
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5).json()
        cookies = health.get("cookies", {})
        st.json({
            "api": "✅ Online",
            "cookies_status": cookies.get("status"),
            "cookies_message": cookies.get("message"),
        })
    except Exception:
        st.error(f"API offline — `{API_BASE_URL}`")
