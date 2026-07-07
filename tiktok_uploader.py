import argparse
import base64
import hashlib
import http.server
import json
import secrets
import threading
import urllib.parse
import webbrowser
from pathlib import Path

import requests

import config

AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INBOX_UPLOAD_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
DIRECT_POST_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"

REDIRECT_URI = "https://jnskoulemou-coder.github.io/animal/callback.html"
REDIRECT_PORT = 8921
SCOPES = "user.info.basic,video.upload,video.publish"
TOKEN_FILE = config.ROOT_DIR / "tiktok_token.json"
TOKEN_REQUEST_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Cache-Control": "no-cache",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}


def _make_pkce_pair():
    # Use a purely alphanumeric verifier (hex digits) - TikTok's PKCE validation has been
    # reported to mishandle the '-'/'_' characters produced by token_urlsafe.
    verifier = secrets.token_hex(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).decode().rstrip("=")
    return verifier, challenge


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    result = {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        # parse_qs treats '+' as a space (form-encoding convention), which would silently
        # corrupt an auth code containing a literal '+'. unquote() only decodes %XX escapes.
        params = {}
        for part in parsed.query.split("&"):
            if "=" in part:
                key, _, value = part.partition("=")
                params[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
        _CallbackHandler.result["code"] = params.get("code")
        _CallbackHandler.result["state"] = params.get("state")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body>Authentication complete. You may close this window.</body></html>")

    def log_message(self, format, *args):
        pass


def _run_oauth_flow() -> dict:
    verifier, challenge = _make_pkce_pair()
    state = secrets.token_urlsafe(16)

    params = {
        "client_key": config.TIKTOK_CLIENT_KEY,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    auth_url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    print(f"Please visit this URL to authorize this application: {auth_url}")
    webbrowser.open(auth_url)

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    thread.join(timeout=300)
    server.server_close()

    code = _CallbackHandler.result.get("code")
    if not code:
        raise RuntimeError("OAuth flow did not complete - no authorization code received")

    response = requests.post(
        TOKEN_URL,
        data={
            "client_key": config.TIKTOK_CLIENT_KEY,
            "client_secret": config.TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        headers=TOKEN_REQUEST_HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    token_data = response.json()
    if "access_token" not in token_data:
        raise RuntimeError(f"Token exchange failed: {token_data}")

    TOKEN_FILE.write_text(json.dumps(token_data))
    return token_data


def _refresh_token(refresh_token: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "client_key": config.TIKTOK_CLIENT_KEY,
            "client_secret": config.TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers=TOKEN_REQUEST_HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    token_data = response.json()
    if "access_token" not in token_data:
        raise RuntimeError(f"Token refresh failed: {token_data}")
    TOKEN_FILE.write_text(json.dumps(token_data))
    return token_data


def _get_access_token() -> str:
    if TOKEN_FILE.exists():
        token_data = json.loads(TOKEN_FILE.read_text())
        try:
            token_data = _refresh_token(token_data["refresh_token"])
            return token_data["access_token"]
        except Exception:
            pass
    token_data = _run_oauth_flow()
    return token_data["access_token"]


MAX_CHUNK_SIZE = 64 * 1024 * 1024  # TikTok FILE_UPLOAD chunk size must be <= 64MB
MIN_CHUNK_SIZE = 5 * 1024 * 1024  # ...and >= 5MB (except when the whole file is one chunk)


def _plan_chunks(video_size: int):
    if video_size <= MAX_CHUNK_SIZE:
        return video_size, 1
    total_chunk_count = -(-video_size // MAX_CHUNK_SIZE)  # ceil division
    chunk_size = -(-video_size // total_chunk_count)  # roughly even chunks
    chunk_size = max(chunk_size, MIN_CHUNK_SIZE)
    return chunk_size, total_chunk_count


def _init_upload(url: str, access_token: str, body: dict) -> tuple[str, str]:
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
    )
    if not response.ok:
        print(f"[DEBUG] init response body: {response.text}")
    response.raise_for_status()
    data = response.json()
    if data.get("error", {}).get("code") != "ok":
        raise RuntimeError(f"Upload init failed: {data}")
    return data["data"]["upload_url"], data["data"]["publish_id"]


def _upload_chunks(upload_url: str, video_path: Path, video_size: int, chunk_size: int, total_chunk_count: int) -> None:
    with open(video_path, "rb") as f:
        for i in range(total_chunk_count):
            start = i * chunk_size
            end = min(start + chunk_size, video_size) - 1
            f.seek(start)
            chunk_bytes = f.read(end - start + 1)

            upload_response = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes {start}-{end}/{video_size}",
                },
                data=chunk_bytes,
                timeout=300,
            )
            if not upload_response.ok:
                print(f"[DEBUG] chunk {i} upload response: {upload_response.text}")
            upload_response.raise_for_status()


def upload_video_draft(video_path: Path) -> str:
    """Upload a video to the authorized creator's TikTok inbox as a draft (not published)."""
    access_token = _get_access_token()
    video_size = video_path.stat().st_size
    chunk_size, total_chunk_count = _plan_chunks(video_size)

    upload_url, publish_id = _init_upload(
        INBOX_UPLOAD_INIT_URL,
        access_token,
        {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            }
        },
    )
    _upload_chunks(upload_url, video_path, video_size, chunk_size, total_chunk_count)

    print(f"Uploaded as draft to TikTok inbox. publish_id={publish_id}")
    return publish_id


def publish_video_direct(video_path: Path, title: str, privacy_level: str = "SELF_ONLY") -> str:
    """Directly publish a video to the authorized account (requires Direct Post capability).
    privacy_level: 'SELF_ONLY' (private, safe for demo/review), 'PUBLIC_TO_EVERYONE', etc."""
    access_token = _get_access_token()
    video_size = video_path.stat().st_size
    chunk_size, total_chunk_count = _plan_chunks(video_size)

    upload_url, publish_id = _init_upload(
        DIRECT_POST_INIT_URL,
        access_token,
        {
            "post_info": {
                "title": title[:150],
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            },
        },
    )
    _upload_chunks(upload_url, video_path, video_size, chunk_size, total_chunk_count)

    print(f"Published directly ({privacy_level}). publish_id={publish_id}")
    return publish_id


def main():
    parser = argparse.ArgumentParser(description="Upload a video to TikTok")
    parser.add_argument("video", help="Path to the mp4 file")
    parser.add_argument("--direct", action="store_true", help="Publish directly instead of as a draft")
    parser.add_argument("--title", default="Second Chance Paws", help="Title for direct post")
    parser.add_argument("--privacy", default="SELF_ONLY", help="Privacy level for direct post")
    args = parser.parse_args()

    if args.direct:
        publish_video_direct(Path(args.video), args.title, args.privacy)
    else:
        upload_video_draft(Path(args.video))


if __name__ == "__main__":
    main()
