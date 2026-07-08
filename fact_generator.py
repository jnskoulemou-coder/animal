import argparse
import json

from anthropic import Anthropic

import config

SYSTEM_PROMPT = """You write vertical-video voice-over scripts (TikTok/Reels/Shorts) about \
biblical characters and stories (Old and New Testament). Write in English, targeting ~60 \
seconds of spoken narration (150-160 words), ready to be read aloud by a text-to-speech voice. \
No markdown, no emojis, no hashtags.

Structure for maximum watch-through and shareability:
- First sentence: a strong hook that creates a question in the viewer's mind (danger, mystery, \
or an emotional stakes-setting moment) - never give away the outcome yet.
- Middle: fast pacing, no filler or dead air, short punchy sentences, building tension or \
curiosity toward a turning point. Stay faithful to the biblical account - do not invent events \
that aren't in scripture, but you may narrate it vividly and dramatically.
- Include the key turning point or revelation from the story.
- End with a short, engaging question to the viewer (e.g. "What would you have done in his \
place?") to encourage comments.

You must also split the narration into exactly 4 scenes for illustration. For each scene, write \
a short visual description (one sentence) suitable for a respectful, painterly biblical \
illustration - always specifying "biblical illustration style, painterly, warm dramatic \
lighting, reverent tone" and naming the characters/setting present.

Respond with ONLY a JSON object, no other text, in this exact shape:
{"narration": "...", "scenes": ["scene 1 description", "scene 2 description", "scene 3 description", "scene 4 description"]}"""


def generate_script(topic: str) -> dict:
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Topic: {topic}"},
        ],
    )
    text_blocks = [block.text for block in message.content if block.type == "text"]
    text = "".join(text_blocks).strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description="Generate a biblical story video script")
    parser.add_argument("topic", help="Topic for the script (e.g. 'David and Goliath')")
    args = parser.parse_args()

    story = generate_script(args.topic)
    print(story["narration"])
    print()
    for i, scene in enumerate(story["scenes"], 1):
        print(f"Scene {i}: {scene}")


if __name__ == "__main__":
    main()
