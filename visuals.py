import argparse
from pathlib import Path

import requests

import config

SEARCH_URL = "https://api.pexels.com/videos/search"


def _pick_best_file(video: dict, target_width: int = 1080) -> dict:
    """Prefer a portrait/vertical file close to the target width (avoids downloading and
    processing needlessly huge 4K/8K source files, which makes per-frame compositing slow)."""
    files = video.get("video_files", [])
    portrait = [f for f in files if f.get("height", 0) > f.get("width", 0)]
    candidates = portrait or files
    at_least_target = [f for f in candidates if f.get("width", 0) >= target_width]
    pool = at_least_target or candidates
    return min(pool, key=lambda f: abs(f.get("width", 0) - target_width))


def search_videos(query: str, count: int = 3) -> list[dict]:
    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {"query": query, "per_page": count, "orientation": "portrait"}
    response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("videos", [])


def fetch_visuals(query: str, count: int = 3, out_dir: Path = None) -> list[Path]:
    out_dir = out_dir or config.ASSETS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    videos = search_videos(query, count)
    saved_paths = []
    for i, video in enumerate(videos):
        file_info = _pick_best_file(video)
        video_url = file_info["link"]
        dest = out_dir / f"visual_{query.replace(' ', '_')}_{i}.mp4"

        response = requests.get(video_url, timeout=60)
        response.raise_for_status()
        dest.write_bytes(response.content)
        saved_paths.append(dest)

    return saved_paths


def main():
    parser = argparse.ArgumentParser(description="Download royalty-free video clips from Pexels")
    parser.add_argument("query", help="Search keyword (e.g. 'dog shelter')")
    parser.add_argument("--count", type=int, default=3, help="Number of clips to download")
    args = parser.parse_args()

    paths = fetch_visuals(args.query, args.count)
    for p in paths:
        print(f"Saved {p}")


if __name__ == "__main__":
    main()
