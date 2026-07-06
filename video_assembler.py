import argparse
from pathlib import Path

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)

import config

FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"
WORDS_PER_CAPTION = 8


def _fit_clip_to_size(clip, size):
    target_w, target_h = size
    scale = max(target_w / clip.w, target_h / clip.h)
    resized = clip.resized(scale)
    cropped = resized.cropped(
        x_center=resized.w / 2, y_center=resized.h / 2, width=target_w, height=target_h
    )
    return cropped


def _build_visual_track(visual_paths, total_duration, size):
    clips = []
    remaining = total_duration
    i = 0
    while remaining > 0:
        source = visual_paths[i % len(visual_paths)]
        clip = VideoFileClip(str(source)).without_audio()
        clip = _fit_clip_to_size(clip, size)
        take = min(clip.duration, remaining)
        clips.append(clip.subclipped(0, take))
        remaining -= take
        i += 1
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


def assemble_video(voice_path: Path, visual_paths: list[Path], script_text: str, output_path: Path) -> Path:
    size = config.VIDEO_SIZE
    audio = AudioFileClip(str(voice_path))
    total_duration = audio.duration

    visual_track = _build_visual_track(visual_paths, total_duration, size)
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
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Assemble a vertical video from voice-over + visuals + script")
    parser.add_argument("output", help="Output mp4 path")
    parser.add_argument("--voice", required=True, help="Path to voice-over mp3")
    parser.add_argument("--script-file", required=True, help="Path to script text file (for captions)")
    parser.add_argument("--visuals", required=True, nargs="+", help="Paths to visual clip files")
    args = parser.parse_args()

    script_text = Path(args.script_file).read_text(encoding="utf-8")
    visual_paths = [Path(v) for v in args.visuals]

    path = assemble_video(Path(args.voice), visual_paths, script_text, Path(args.output))
    print(f"Saved video to {path}")


if __name__ == "__main__":
    main()
