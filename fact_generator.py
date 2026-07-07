import argparse

from anthropic import Anthropic

import config

SYSTEM_PROMPT = """You write vertical-video voice-over scripts (TikTok/Reels/Shorts) \
about rescue animals, shelters, and pet adoption. Write in English, targeting ~60 seconds \
of spoken narration (150-160 words), ready to be read aloud by a text-to-speech voice. \
No markdown, no emojis, no hashtags.

Structure for maximum watch-through and shareability:
- First sentence: a strong hook that creates a question in the viewer's mind (danger, \
mystery, or an emotional stakes-setting moment) - never give away the outcome yet.
- Middle: fast pacing, no filler or dead air, short punchy sentences, building tension \
or curiosity toward a turning point.
- Include one genuine twist, surprising detail, or reveal partway through or near the \
end that the viewer wouldn't expect from the hook alone.
- End with a short, engaging question to the viewer (e.g. "Would you have adopted her?") \
to encourage comments.

Output ONLY the script itself - no title, no intro like "Here's a script", no labels, \
no commentary before or after."""


def generate_script(topic: str) -> str:
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Topic: {topic}"},
        ],
    )
    return message.content[0].text.strip()


def format_provided_story(story_text: str) -> str:
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=400,
        system="You lightly edit real rescue-animal stories into a ~60 second "
        "(150-160 word) voice-over script for a vertical video. Keep every fact from "
        "the original story exactly as given - do not invent new details. English, "
        "simple spoken language, no markdown, no emojis, no hashtags. End with a short, "
        "engaging question to the viewer to encourage comments.",
        messages=[
            {"role": "user", "content": story_text},
        ],
    )
    return message.content[0].text.strip()


def main():
    parser = argparse.ArgumentParser(description="Generate a rescue-animal video script")
    parser.add_argument("topic", help="Topic for the script (e.g. 'how shelters evaluate dogs')")
    parser.add_argument(
        "--story",
        action="store_true",
        help="Treat the topic argument as a real story to format, instead of generating facts",
    )
    args = parser.parse_args()

    script = format_provided_story(args.topic) if args.story else generate_script(args.topic)
    print(script)


if __name__ == "__main__":
    main()
