import config
import main
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
    return f"{topic[0].upper()}{topic[1:]} | Second Chance Paws"


def run_daily():
    index = _next_index()
    entry = TOPICS[index]
    print(f"[daily_task] Topic {index + 1}/{len(TOPICS)}: {entry['topic']}")
    result = main.run(entry["topic"], entry["visual_query"])

    title = _make_title(result["topic"])
    description = f"{result['script']}\n\n#rescueanimals #animalrescue #petadoption"

    print("Uploading to YouTube (public)...")
    youtube_uploader.upload_video(
        result["video_path"],
        title=title,
        description=description,
        tags=["rescue animals", "animal rescue", "pet adoption", "wildlife rescue"],
        privacy_status="public",
    )


if __name__ == "__main__":
    run_daily()
