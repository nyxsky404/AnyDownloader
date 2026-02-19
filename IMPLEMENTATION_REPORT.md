# YouTube Bot Detection Solution - Technical Report

## Executive Summary

We successfully implemented a video downloader API supporting YouTube, Twitter/X, and Facebook. The main challenge was YouTube's bot detection and rate limiting, which caused "Sign in to confirm you're not a bot" errors. After evaluating multiple approaches, we implemented cookies-based authentication as the most reliable, production-ready solution.

---

## Problem Statement

### Initial Error
```
ERROR: [youtube] [video_id]: Sign in to confirm you're not a bot. This helps protect our community. Learn more
```

### Secondary Issues
- HTTP Error 429: Too Many Requests (rate limiting)
- Twitter/X API returning "Dependency: Unspecified" errors
- Download failures on cloud platforms (Render) due to shared IPs

---

## Approaches Evaluated

### 1. Rate Limiting & Delays ❌

**Implementation:**
```python
ydl_opts = {
    'sleep_interval': 5,
    'max_sleep_interval': 15,
    'sleep_requests': 1,
}
```

**Outcome:** Partial fix only
- Reduced rate limit hits
- Did NOT solve "Sign in to confirm you're not a bot" error
- YouTube still blocks anonymous access from cloud IPs

**Why it failed:** YouTube requires authentication, not just rate limiting

---

### 2. PO Token (Proof of Origin Token) ❌

**Research:** Referenced [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)

**Approach:** Generate PO tokens automatically to bypass bot detection

**Challenges Identified:**
- PO tokens are short-lived (days to weeks)
- Requires manual browser interaction to extract
- Complex automation needed
- Requires separate token refresh mechanism

**Why rejected:** Adds complexity without solving authentication requirement

---

### 3. Headless Browser Automation ❌

**Reference:** https://github.com/yt-dlp/yt-dlp/issues/10128

**Approach:** Use Playwright/Puppeteer with headless Chrome to:
- Automate login flow
- Pass authenticated requests
- Auto-refresh cookies

**Implementation Consideration:**
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # Login and extract cookies
```

**Drawbacks:**
- Docker image size: +800MB (Chromium)
- Slower downloads (browser overhead)
- Can still be detected (bot patterns)
- Maintenance overhead for browser updates
- Account risk (using real credentials in automation)

**Why rejected:** Overkill, resource-heavy, still vulnerable to detection

---

### 4. OAuth Login ❌

**Reference:** [yt-dlp Wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#logging-in-with-oauth)

**Status:** Deprecated - no longer works with YouTube

**Quote:** "Due to new restrictions enacted by YouTube, logging in with OAuth no longer works with yt-dlp. You should use cookies instead."

---

## Final Solution: Cookies-Based Authentication ✅

### Architecture

```
Local Browser (Chrome)
    ↓ Export cookies via extension
cookies.txt → Docker volume mount → App reads cookies
    ↓
yt-dlp uses cookies for authenticated requests
    ↓
Successful downloads from YouTube
```

### Implementation Details

**1. Cookie Export**

**Method A: Browser Extension (Recommended)**
- Install "Get cookies.txt LOCALLY" extension
- Use **incognito** window for YouTube
- Navigate to `youtube.com/robots.txt` (prevents rotation)
- Export cookies
- Close incognito immediately (never reopen)

**Method B: yt-dlp Built-in**
```bash
yt-dlp --cookies-from-browser chrome "https://youtube.com" --print-to-file "%(cookies)s" cookies.txt
```

**2. Cookie Storage Options**

| Environment | Storage Method | Path |
|-------------|----------------|------|
| Local/Docker | File mount | `./cookies.txt` |
| Render | Environment variable | `YT_DLP_COOKIES_CONTENT` (as string) |

**3. Cookie Validation**

Implemented `cookies_checker.py`:
- Checks file existence
- Parses YouTube auth cookies (`SID`, `HSID`, `SSID`, `APISID`, `SAPISID`, `SIDCC`, `LOGIN_INFO`)
- Calculates expiry dates from auth cookies (not session cookies)
- 2 endpoints:
  - `GET /cookies/status` - Fast file/parses check
  - `GET /cookies/test` - Actual YouTube request validation

**4. yt-dlp Configuration**
```python
ydl_opts = {
    'cookiefile': str(settings.YT_DLP_COOKIES_FILE),
    'sleep_interval': 5,  # Rate limiting (backup)
    'max_sleep_interval': 15,
    'sleep_requests': 1,
}
```

---

## Why We Chose Cookies

| Factor | Cookies | PO Token | Headless |
|--------|---------|----------|----------|
| **Complexity** | Low | High | Very High |
| **Docker Size** | No increase | No increase | +800MB |
| **Reliability** | High (3-6 months) | Low (days) | Medium |
| **Maintenance** | Refresh every 3 months | Auto-refresh needed | Browser updates |
| **Production Ready** | ✅ Yes | ⚠️ Requires automation | ⚠️ Heavy |
| **Cloud Compatible** | ✅ Yes (env var) | ✅ Yes | ⚠️ Heavy |

**Decision:** Cookies are the most production-ready, maintainable solution.

---

## Cookie Best Practices (Critical)

### The Problem: Cookie Rotation

YouTube rotates cookies when:
- Same browser accesses YouTube with different sessions
- User logs in/out
- Multiple tabs on same account

### Our Solution: Isolated Export

**From [yt-dlp Wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies):**

> "YouTube rotates account cookies frequently on open YouTube browser tabs as a security measure."

**Best Practice Implemented:**
1. Use **dedicated Google account** (not personal account)
2. Export from **incognito window only**
3. Navigate to `youtube.com/robots.txt` (static page, no state change)
4. Export cookies, **close incognito immediately**
5. Never reopen that session

**Result:** Cookies last **3-6 months** instead of hours/days

---

## Twitter/X Download Issue

### Problem
```
ERROR: [twitter] [status_id]: Error(s) while querying API: Dependency: Unspecified
```

### Root Cause
- yt-dlp version issue (pre-2026.02.19)
- Twitter API changes

### Solution
1. Use **nightly pre-release** version of yt-dlp:
   ```dockerfile
   pip install --no-cache-dir --upgrade --pre "yt-dlp[default]"
   ```
2. Referenced: [GitHub Issue #15963](https://github.com/yt-dlp/yt-dlp/issues/15963) - Fixed in nightly

### Status
- ✅ Fixed in nightly builds (2026.02.19+)
- Verified working with test videos

---

## Platform Support

| Platform | Status | Auth Required |
|----------|--------|---------------|
| YouTube | ✅ Working | Yes (cookies) |
| YouTube Shorts | ✅ Working | Yes (cookies) |
| Twitter/X | ✅ Working | No |
| Facebook | ✅ Working | No |

---

## Rate Limits (Documented)

From [yt-dlp Known Issues](https://github.com/yt-dlp/yt-dlp/issues/3766):

| Session Type | Rate Limit |
|--------------|------------|
| Guest (no cookies) | ~300 videos/hour |
| Account (with cookies) | ~2000 videos/hour |

Our API adds 5-15 second delays as backup protection.

---

## Deployment Configuration

### Docker (`Dockerfile`)
```dockerfile
FROM python:3.12-slim
# Install yt-dlp nightly for Twitter fix
RUN pip install --no-cache-dir --upgrade --pre "yt-dlp[default]"
```

### Docker Compose (`docker-compose.yml`)
```yaml
volumes:
  - ./cookies.txt:/app/cookies.txt  # Mount cookies file
```

### Render (Cloud Deployment)
```bash
# Environment variables:
YT_DLP_COOKIES_FILE=/app/downloads/cookies.txt
YT_DLP_COOKIES_CONTENT=<paste cookies content here>
```

---

## Monitoring & Maintenance

### Cookie Status Endpoints

**Quick Check:**
```bash
curl http://localhost:8000/cookies/status
```
Response:
```json
{
  "exists": true,
  "status": "valid",
  "message": "Cookies valid for 91 more days",
  "cookie_count": 15,
  "expires_at": "2026-05-20T00:00:00",
  "days_until_expiry": 91
}
```

**Full Validation:**
```bash
curl http://localhost:8000/cookies/test
```
Same as above, but actually tests with YouTube.

### Maintenance Schedule

| Task | Frequency |
|------|-----------|
| Check cookie status | Monthly |
| Refresh cookies | Every 3 months |
| Update yt-dlp version | Quarterly |

---

## Security Considerations

### Account Security
- ✅ Using **dedicated throwaway account**
- ✅ Not using personal account
- ✅ Cookies stored in `.gitignore`
- ✅ Render uses environment variable (not in code)

### File Security
```
.gitignore includes:
- cookies.txt
- .env (contains YT_DLP_COOKIES_CONTENT)
- downloads/ (videos)
```

---

## References

1. [yt-dlp YouTube Extractors Wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)
2. [yt-dlp Known Issues #3766](https://github.com/yt-dlp/yt-dlp/issues/3766)
3. [Twitter Bug Fix #15963](https://github.com/yt-dlp/yt-dlp/issues/15963)
4. [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
5. [YouTube "Sign in to confirm you're not a bot" #10128](https://github.com/yt-dlp/yt-dlp/issues/10128)
6. [Cookie Rotation Issue #8227](https://github.com/yt-dlp/yt-dlp/issues/8227)
7. [Rate Limit Issue #11426](https://github.com/yt-dlp/yt-dlp/issues/11426)

---

## Conclusion

After evaluating multiple approaches (rate limiting, PO tokens, headless browsers, OAuth), we implemented **cookies-based authentication** as it provides:

- ✅ Most reliable solution (3-6 month cookie lifecycle)
- ✅ Lowest maintenance (refresh every 3 months)
- ✅ Production-ready for cloud deployment
- ✅ Compatible with Docker and Render
- ✅ Respects yt-dlp best practices
- ✅ Uses dedicated account for security

The Twitter/X download issue was resolved by using yt-dlp nightly builds, which include the API fix.

---

## Appendix: File Structure

```
Video/
├── config.py              # Settings, cookie file creation
├── cookies_checker.py      # Cookie validation logic
├── downloader.py          # Main download functionality
├── api.py                 # FastAPI endpoints
├── models.py              # Pydantic models, URL validation
├── Dockerfile             # Container with yt-dlp nightly
├── docker-compose.yml     # Local development
├── requirements.txt       # Dependencies
├── cookies.txt            # YouTube cookies (gitignored)
├── .env                   # Environment vars (gitignored)
├── .gitignore             # Excludes sensitive files
└── README.md              # User documentation
```

---
