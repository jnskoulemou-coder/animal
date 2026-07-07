import argparse
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRET_FILE = config.ROOT_DIR / "client_secret.json"
TOKEN_FILE = config.ROOT_DIR / "token.json"


def _get_credentials() -> Credentials:
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def upload_video(
    video_path: Path,
    title: str,
    description: str = "",
    tags: list[str] = None,
    privacy_status: str = "private",
) -> str:
    """Upload a video to the authenticated channel. privacy_status: 'private', 'unlisted', or 'public'."""
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or [],
            "categoryId": "15",  # Pets & Animals
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Uploaded: https://www.youtube.com/watch?v={video_id}")
    return video_id


def set_privacy(video_id: str, privacy_status: str) -> None:
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)
    youtube.videos().update(
        part="status",
        body={"id": video_id, "status": {"privacyStatus": privacy_status}},
    ).execute()
    print(f"Video {video_id} privacy set to {privacy_status}")


def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube")
    parser.add_argument("video", help="Path to the mp4 file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", nargs="*", default=[], help="Video tags")
    parser.add_argument(
        "--privacy",
        default="private",
        choices=["private", "unlisted", "public"],
        help="Visibility (default: private, for safe testing)",
    )
    args = parser.parse_args()

    upload_video(Path(args.video), args.title, args.description, args.tags, args.privacy)


if __name__ == "__main__":
    main()
