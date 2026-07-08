import argparse
import json

from anthropic import Anthropic

import config

SYSTEM_PROMPT = """You write vertical-video voice-over scripts (TikTok/Reels/Shorts) about \
biblical characters and stories (Old and New Testament). Write in English, targeting ~60-75 \
seconds of spoken narration (160-190 words), ready to be read aloud by a text-to-speech voice. \
No markdown, no emojis, no hashtags.

The story MUST be told completely, from its beginning to its actual conclusion in scripture - \
never cut off partway through or leave the outcome implied. If the full story cannot fit \
naturally, pick a self-contained episode of it that still has a clear beginning, middle, and \
end within this one video (do not promise a "part 2").

Structure for maximum watch-through and shareability, mapped across exactly 5 scenes:
- Scene 1 (setup): a strong hook that creates a question in the viewer's mind (danger, mystery, \
or an emotional stakes-setting moment) - establish who and where, never give away the outcome yet.
- Scene 2 (rising action): the conflict or challenge develops, fast pacing, no filler or dead air.
- Scene 3 (turning point): the key decision, confrontation, or divine intervention of the story.
- Scene 4 (climax): the story's peak moment - the actual resolution of the conflict (e.g. the \
stone striking Goliath, Samson pushing the pillars, the tomb found empty).
- Scene 5 (conclusion): the aftermath and what it means, ending with a short, engaging question \
to the viewer (e.g. "What would you have done in his place?") to encourage comments.

Stay faithful to the biblical account - do not invent events that aren't in scripture, but you \
may narrate it vividly and dramatically.

For each of the 5 scenes, write a short visual description (one sentence) suitable for a \
respectful, painterly biblical illustration - always specifying "biblical illustration style, \
painterly, warm dramatic lighting, reverent tone" and naming the characters/setting present.

Respond with ONLY a JSON object, no other text, in this exact shape:
{"narration": "...", "scenes": ["scene 1 description", "scene 2 description", "scene 3 description", "scene 4 description", "scene 5 description"]}"""


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
