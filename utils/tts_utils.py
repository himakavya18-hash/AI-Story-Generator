"""Helpers for turning generated story text into spoken audio."""

from pathlib import Path


def text_to_speech(
    text: str,
    output_file: str | Path = "static/audio/story.wav",
    *,
    rate: int = 175,
    volume: float = 1.0,
) -> Path:
    """Save *text* as a WAV audio file and return its path.

    This uses ``pyttsx3``, which relies on the voices installed on the
    computer and therefore does not require an API key or an internet
    connection.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if not 0.0 <= volume <= 1.0:
        raise ValueError("volume must be between 0.0 and 1.0")
    if rate <= 0:
        raise ValueError("rate must be greater than zero")

    try:
        import pyttsx3
    except ImportError as error:
        raise RuntimeError(
            "pyttsx3 is not installed. Run: pip install -r requirements.txt"
        ) from error

    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)
    engine.save_to_file(text.strip(), str(destination))
    engine.runAndWait()

    return destination
