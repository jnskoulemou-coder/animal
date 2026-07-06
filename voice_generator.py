import argparse
import asyncio
from pathlib import Path

import edge_tts

DEFAULT_VOICE = "en-US-AriaNeural"


async def _synthesize(text: str, output_path: Path, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def generate_voice(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize(text, output_path, voice))
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate English voice-over audio from a script")
    parser.add_argument("output", help="Output mp3 path (e.g. assets/voice.mp3)")
    parser.add_argument("--text", help="Script text to narrate")
    parser.add_argument("--text-file", help="Path to a text file containing the script")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"edge-tts voice name (default: {DEFAULT_VOICE})")
    args = parser.parse_args()

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        parser.error("Provide either --text or --text-file")

    path = generate_voice(text, Path(args.output), args.voice)
    print(f"Saved voice-over to {path}")


if __name__ == "__main__":
    main()
