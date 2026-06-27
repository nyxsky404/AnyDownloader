import logging
from pathlib import Path
from typing import Dict
import yt_dlp

from config import settings
from cookies_checker import check_cookies

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VideoDownloader:
    
    def __init__(self):
        self.download_dir = settings.LOCAL_DOWNLOAD_DIR
        
        cookies_status = check_cookies(settings.YT_DLP_COOKIES_FILE)
        if cookies_status.status == "valid":
            logger.info(f"Cookies valid: {cookies_status.message}")
        elif cookies_status.status == "expiring_soon":
            logger.warning(f"Cookies expiring soon: {cookies_status.message}")
        elif cookies_status.status == "expired":
            logger.error(f"Cookies EXPIRED: {cookies_status.message} - Refresh immediately!")
        elif cookies_status.status == "missing":
            logger.warning("No cookies file - YouTube may block downloads")
        else:
            logger.warning(f"Cookies status: {cookies_status.message}")
        
        logger.info(f"Local storage: {self.download_dir}")
    
    def _build_ydl_opts(self, output_path, fmt: str) -> dict:
        opts = {
            'format': fmt,
            'format_sort': ['res:2160', 'ext:mp4:m4a', 'codec:h264'],
            'outtmpl': str(output_path),
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'noplaylist': False,
            'yes_playlist': True,
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'socket_timeout': settings.DOWNLOAD_TIMEOUT,
            'retries': settings.YT_DLP_MAX_RETRIES,
            'max_filesize': settings.YT_DLP_MAX_FILESIZE * 1024 * 1024,
            'logger': logger,
            'js_runtimes': {'node': {}},
            'sleep_interval': 5,
            'max_sleep_interval': 15,
            'sleep_requests': 1,
        }
        if settings.cookies_file_exists:
            opts['cookiefile'] = str(settings.YT_DLP_COOKIES_FILE)
        return opts

    def _make_progress_hook(self, log_queue=None):
        current_file = [None]

        def _emit(msg: str, level: str = "info"):
            if level == "error":
                logger.error(msg)
            else:
                logger.info(msg)
            if log_queue is not None:
                log_queue.put({"type": "log", "message": msg})

        def hook(d):
            status = d.get('status')
            filename = d.get('filename', '')
            info = d.get('info_dict', {})
            title = info.get('title') or Path(filename).stem or 'unknown'
            playlist_index = info.get('playlist_index')
            playlist_count = info.get('n_entries') or info.get('playlist_count')

            prefix = f"[{playlist_index}/{playlist_count}] " if playlist_index else ""

            if status == 'downloading' and filename != current_file[0]:
                current_file[0] = filename
                _emit(f"{prefix}Download started: {title}")
            elif status == 'finished':
                _emit(f"{prefix}Download complete: {title}")
            elif status == 'error':
                _emit(f"{prefix}Download error: {title}", level="error")

        return hook

    def download(self, url: str, log_queue=None) -> Dict:
        logger.info(f"Starting download for URL: {url}")

        format_attempts = [
            'bestvideo*+bestaudio*/best*',
            'bestvideo+bestaudio/best',
            'best',
        ]

        try:
            output_template = "%(playlist_index|)svideo_%(id)s.%(ext)s"
            output_path = self.download_dir / output_template

            info = None
            last_ydl = None
            last_error = None
            progress_hook = self._make_progress_hook(log_queue)

            for fmt in format_attempts:
                try:
                    ydl_opts = self._build_ydl_opts(output_path, fmt)
                    ydl_opts['progress_hooks'] = [progress_hook]
                    ydl = yt_dlp.YoutubeDL(ydl_opts)
                    logger.info(f"Trying format: {fmt}")
                    info = ydl.extract_info(url, download=True)
                    last_ydl = ydl
                    break
                except Exception as e:
                    if 'Requested format is not available' in str(e):
                        logger.warning(f"Format '{fmt}' unavailable, trying next fallback")
                        last_error = e
                        continue
                    raise

            if info is None:
                raise last_error

            is_playlist = 'entries' in info

            if is_playlist:
                entries = list(info['entries'])
                logger.info(f"Playlist download successful: {len(entries)} videos")

                filenames = []
                download_urls = []

                for entry in entries:
                    if entry:
                        filename = last_ydl.prepare_filename(entry)
                        if not filename.endswith('.mp4'):
                            filename = filename.rsplit('.', 1)[0] + '.mp4'
                        filepath = Path(filename)
                        if filepath.exists():
                            filenames.append(filepath.name)
                            download_urls.append(f"/downloads/{filepath.name}")

                return {
                    'status': 'success',
                    'type': 'playlist',
                    'platform': info.get('extractor', ''),
                    'playlist_title': info.get('title', ''),
                    'video_count': len(filenames),
                    'filenames': filenames,
                    'download_urls': download_urls,
                }
            else:
                filename = last_ydl.prepare_filename(info)
                if not filename.endswith('.mp4'):
                    filename = filename.rsplit('.', 1)[0] + '.mp4'
                filepath = Path(filename)

                if not filepath.exists():
                    raise FileNotFoundError(f"Downloaded file not found: {filepath}")

                logger.info(f"Download successful: {filepath.name}")

                return {
                    'status': 'success',
                    'type': 'video',
                    'platform': info.get('extractor', ''),
                    'video_title': info.get('title', ''),
                    'filename': filepath.name,
                    'download_url': f"/downloads/{filepath.name}"
                }

        except Exception as e:
            if "DownloadError" in type(e).__name__:
                logger.error(f"Download error: {str(e)}")
                raise Exception(f"Failed to download video: {str(e)}")
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise Exception(f"Error during download: {str(e)}")
