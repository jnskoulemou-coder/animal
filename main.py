import argparse
import shutil
from pathlib import Path

import config
import fact_generator
import video_assembler
import visuals
import voice_generator

DOWNLOADS_DIR = Path.home() / "Downloads"


def run(topic: str, visual_query: str = None) -> dict:
    visual_query = visual_query or topic

    print(f"Generating script for: {topic}")
    script = fact_generator.generate_script(topic)
    print(script)

    slug = topic.lower().replace(" ", "_")[:40]
    script_path = config.ASSETS_DIR / f"{slug}_script.txt"
    script_path.write_text(script, encoding="utf-8")

    print("Generating voice-over...")
    voice_path = config.ASSETS_DIR / f"{slug}_voice.mp3"
    voice_generator.generate_voice(script, voice_path)

    print(f"Fetching visuals for: {visual_query}")
    visual_paths = visuals.fetch_visuals(visual_query, count=3)

    print("Assembling final video...")
    output_path = config.OUTPUT_DIR / f"{slug}.mp4"
    video_assembler.assemble_video(voice_path, visual_paths, script, output_path)

    print(f"Done: {output_path}")

    downloads_copy = DOWNLOADS_DIR / output_path.name
    shutil.copy2(output_path, downloads_copy)
    print(f"Copied to {downloads_copy}")

    return {"video_path": output_path, "script": script, "topic": topic}


def main():
    parser = argparse.ArgumentParser(description="Generate a full rescue-animal video from a topic")
    parser.add_argument("topic", help="Topic for the script (e.g. 'why shelter cats hide when scared')")
    parser.add_argument("--visual-query", help="Override the keyword used to search Pexels visuals")
    args = parser.parse_args()

    run(args.topic, args.visual_query)


if __name__ == "__main__":
    main()
