import argparse
import shutil
from pathlib import Path

import config
import fact_generator
import image_generator
import video_assembler
import voice_generator

DOWNLOADS_DIR = Path.home() / "Downloads"


def run(topic: str) -> dict:
    print(f"Generating script for: {topic}")
    story = fact_generator.generate_script(topic)
    print(story["narration"])

    slug = topic.lower().replace(" ", "_")[:40]
    script_path = config.ASSETS_DIR / f"{slug}_script.txt"
    script_path.write_text(story["narration"], encoding="utf-8")

    print("Generating voice-over...")
    voice_path = config.ASSETS_DIR / f"{slug}_voice.mp3"
    voice_generator.generate_voice(story["narration"], voice_path)

    print("Generating scene illustrations...")
    scene_paths = []
    for i, scene in enumerate(story["scenes"]):
        scene_path = config.ASSETS_DIR / f"{slug}_scene{i + 1}.png"
        image_generator.generate_image(scene, scene_path)
        scene_paths.append(scene_path)

    print("Assembling final video...")
    output_path = config.OUTPUT_DIR / f"{slug}.mp4"
    video_assembler.assemble_video(voice_path, scene_paths, story["narration"], output_path)

    print(f"Done: {output_path}")

    downloads_copy = DOWNLOADS_DIR / output_path.name
    shutil.copy2(output_path, downloads_copy)
    print(f"Copied to {downloads_copy}")

    return {
        "video_path": output_path,
        "downloads_copy": downloads_copy,
        "script_path": script_path,
        "voice_path": voice_path,
        "scene_paths": scene_paths,
        "script": story["narration"],
        "topic": topic,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate a full biblical story video from a topic")
    parser.add_argument("topic", help="Topic for the script (e.g. 'David and Goliath')")
    args = parser.parse_args()

    run(args.topic)


if __name__ == "__main__":
    main()
