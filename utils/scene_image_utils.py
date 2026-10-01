"""Generate cinematic scene images for a story using the OpenAI Image API."""

import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

_IMAGE_GENERATOR = (
    Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    / "skills/.system/imagegen/scripts/image_gen.py"
)


def _split_into_scenes(text: str, maximum_scenes: int = 4) -> list[str]:
    """Group the story into a small number of visually meaningful scenes."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    scenes: list[str] = []
    current_scene: list[str] = []
    word_count = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())
        if current_scene and word_count + sentence_words > 90:
            scenes.append(" ".join(current_scene))
            current_scene = [sentence]
            word_count = sentence_words
        else:
            current_scene.append(sentence)
            word_count += sentence_words

    if current_scene:
        scenes.append(" ".join(current_scene))

    return scenes[:maximum_scenes] or [text.strip()]


def create_story_scene_images(text: str, output_directory: str | Path) -> list[Path]:
    """Create dramatic landscape images for story scenes and return their paths."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured in the .env file")
    if api_key.startswith("gsk_"):
        raise RuntimeError(
            "OPENAI_API_KEY contains a Groq key. Replace it with an OpenAI API key "
            "from https://platform.openai.com/api-keys."
        )
    if not _IMAGE_GENERATOR.is_file():
        raise RuntimeError("The OpenAI image-generation helper could not be found")

    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    scenes = _split_into_scenes(text)
    image_paths: list[Path] = []

    for index, scene in enumerate(scenes, start=1):
        image_path = destination / f"scene-{index}.png"
        prompt = (
            "Create a cinematic dramatic story scene based on this excerpt. "
            "Use expressive characters, a clear setting, emotional lighting, and a "
            "wide landscape composition suitable for a narrated video. Keep the visual "
            "style consistent across scenes: polished cinematic digital illustration. "
            "Do not include captions, speech bubbles, logos, watermarks, or any text. "
            f"Story excerpt: {scene}"
        )
        command = [
            sys.executable,
            str(_IMAGE_GENERATOR),
            "generate",
            "--model",
            "gpt-image-2",
            "--prompt",
            prompt,
            "--size",
            "1536x1024",
            "--quality",
            "low",
            "--output-format",
            "png",
            "--out",
            str(image_path),
            "--force",
            "--use-case",
            "illustration-story",
            "--constraints",
            "cinematic drama; no text; no logos; no watermark",
        ]
        environment = os.environ.copy()
        environment["OPENAI_API_KEY"] = api_key
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        if result.returncode != 0 or not image_path.is_file():
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            if "AuthenticationError" in detail or "invalid_api_key" in detail:
                raise RuntimeError(
                    "OpenAI rejected OPENAI_API_KEY. Create a valid key at "
                    "https://platform.openai.com/api-keys and update the .env file."
                )
            raise RuntimeError(f"Scene {index} could not be generated: {detail}")
        image_paths.append(image_path)

    return image_paths
