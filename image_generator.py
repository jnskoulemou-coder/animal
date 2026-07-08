import argparse
from pathlib import Path

import requests

import config

GENERATE_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"

STYLE_SUFFIX = ", biblical illustration style, painterly, warm dramatic lighting, reverent tone, no text"


def generate_image(prompt: str, output_path: Path, aspect_ratio: str = "9:16") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    full_prompt = prompt if "biblical illustration style" in prompt else f"{prompt}{STYLE_SUFFIX}"

    response = requests.post(
        GENERATE_URL,
        headers={
            "authorization": f"Bearer {config.STABILITY_API_KEY}",
            "accept": "image/*",
        },
        files={"none": ""},
        data={
            "prompt": full_prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
            "style_preset": "cinematic",
        },
        timeout=60,
    )
    if not response.ok:
        print(f"[DEBUG] Stability response: {response.status_code} {response.text}")
    response.raise_for_status()

    output_path.write_bytes(response.content)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate a biblical-style illustration from a text prompt")
    parser.add_argument("prompt", help="Scene description")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--aspect-ratio", default="9:16", help="Image aspect ratio (default: 9:16)")
    args = parser.parse_args()

    path = generate_image(args.prompt, Path(args.output), args.aspect_ratio)
    print(f"Saved image to {path}")


if __name__ == "__main__":
    main()
