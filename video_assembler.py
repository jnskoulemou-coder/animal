import argparse
import random
from pathlib import Path

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
)
from moviepy import concatenate_videoclips

import config

FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"
WORDS_PER_CAPTION = 8
ZOOM_MARGIN = 1.45  # how much bigger than the frame the image is scaled, to allow pan/zoom


def _ken_burns_clip(image_path: Path, duration: float, size: tuple) -> CompositeVideoClip:
    target_w, target_h = size
    base = ImageClip(str(image_path)).with_duration(duration)

    cover_scale = max(target_w / base.w, target_h / base.h) * ZOOM_MARGIN
    base = base.resized(cover_scale)

    zoom_in = random.choice([True, False])
    start_scale, end_scale = (1.0, 1.3) if zoom_in else (1.3, 1.0)

    max_dx = base.w * (1 - 1 / ZOOM_MARGIN) / 2
    max_dy = base.h * (1 - 1 / ZOOM_MARGIN) / 2
    start_pos = (random.uniform(-max_dx, max_dx), random.uniform(-max_dy, max_dy))
    end_pos = (random.uniform(-max_dx, max_dx), random.uniform(-max_dy, max_dy))

    def scaled_frame(t):
        progress = t / duration
        return start_scale + (end_scale - start_scale) * progress

    def position(t):
        progress = t / duration
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        return (target_w / 2 - base.w / 2 + x, target_h / 2 - base.h / 2 + y)

    animated = base.resized(lambda t: scaled_frame(t)).with_position(position)
    return CompositeVideoClip([animated], size=size).with_duration(duration)


def _build_visual_track(scene_image_paths: list[Path], total_duration: float, size: tuple):
    scene_duration = total_duration / len(scene_image_paths)
    clips = [_ken_burns_clip(path, scene_duration, size) for path in scene_image_paths]
    return concatenate_videoclips(clips, method="compose")


def _build_captions(script_text, total_duration, size):
    words = script_text.split()
    chunks = [
        " ".join(words[i : i + WORDS_PER_CAPTION])
        for i in range(0, len(words), WORDS_PER_CAPTION)
    ]
    chunk_duration = total_duration / len(chunks)

    captions = []
    for idx, chunk in enumerate(chunks):
        txt_clip = TextClip(
            font=FONT_PATH,
            text=chunk,
            font_size=64,
            color="white",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(int(size[0] * 0.85), None),
            text_align="center",
        )
        txt_clip = txt_clip.with_start(idx * chunk_duration).with_duration(chunk_duration)
        txt_clip = txt_clip.with_position(("center", "center"))
        captions.append(txt_clip)
    return captions


def assemble_video(voice_path: Path, scene_image_paths: list[Path], script_text: str, output_path: Path) -> Path:
    size = config.VIDEO_SIZE
    audio = AudioFileClip(str(voice_path))
    total_duration = audio.duration

    visual_track = _build_visual_track(scene_image_paths, total_duration, size)
    captions = _build_captions(script_text, total_duration, size)

    final = CompositeVideoClip([visual_track] + captions, size=size)
    final = final.with_duration(total_duration).with_audio(audio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="veryfast",
        threads=4,
    )
    final.close()
    audio.close()
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Assemble a Ken Burns biblical video from still images + voice-over")
    parser.add_argument("output", help="Output mp4 path")
    parser.add_argument("--voice", required=True, help="Path to voice-over mp3")
    parser.add_argument("--script-file", required=True, help="Path to script text file (for captions)")
    parser.add_argument("--images", required=True, nargs="+", help="Paths to scene image files, in order")
    args = parser.parse_args()

    script_text = Path(args.script_file).read_text(encoding="utf-8")
    image_paths = [Path(v) for v in args.images]

    path = assemble_video(Path(args.voice), image_paths, script_text, Path(args.output))
    print(f"Saved video to {path}")


if __name__ == "__main__":
    main()
