from pathlib import Path

import config
import main
import tiktok_uploader
import youtube_uploader
from topics import TOPICS

STATE_FILE = config.ROOT_DIR / ".topic_index"


def _next_index() -> int:
    if STATE_FILE.exists():
        index = int(STATE_FILE.read_text().strip() or "0")
    else:
        index = 0
    STATE_FILE.write_text(str((index + 1) % len(TOPICS)))
    return index % len(TOPICS)


def _make_title(topic: str) -> str:
    return f"{topic} | Revival"


def run_daily():
    index = _next_index()
    topic = TOPICS[index]
    print(f"[daily_task] Topic {index + 1}/{len(TOPICS)}: {topic}")
    result = main.run(topic)

    title = _make_title(result["topic"])
    description = f"{result['script']}\n\n#biblestory #biblical #christian #faith"

    print("Uploading to YouTube (public)...")
    youtube_uploader.upload_video(
        result["video_path"],
        title=title,
        description=description,
        tags=["bible story", "biblical", "christian", "faith", "scripture"],
        privacy_status="public",
    )

    print("Uploading to TikTok (draft, needs manual publish in-app)...")
    tiktok_uploader.upload_video_draft(result["video_path"])

    _cleanup(result)


def _cleanup(result: dict) -> None:
    """Remove the generated video and intermediate files once both uploads succeeded,
    so finished videos don't pile up and fill the disk."""
    paths_to_remove = [
        result["video_path"],
        result["downloads_copy"],
        result["script_path"],
        result["voice_path"],
        *result["scene_paths"],
    ]
    for path in paths_to_remove:
        path = Path(path)
        if path.exists():
            try:
                path.unlink()
            except OSError as e:
                print(f"Could not delete {path}: {e}")
    print("Cleaned up local video and working files.")


if __name__ == "__main__":
    run_daily()
