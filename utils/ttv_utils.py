"""Create a narrated MP4 video from scene images and a WAV narration file."""

from pathlib import Path


def images_to_video(
    image_files: list[str | Path],
    audio_file: str | Path,
    output_file: str | Path = "static/video/story.mp4",
) -> Path:
    """Create an MP4 from dramatic scene images and supplied narration audio."""
    if not image_files:
        raise ValueError("image_files must contain at least one scene image")

    audio_path = Path(audio_file)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Narration audio was not found: {audio_path}")

    try:
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
    except ImportError as error:
        raise RuntimeError(
            "Video dependencies are missing. Run: pip install -r requirements.txt"
        ) from error

    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1280, 720
    scene_paths = [Path(image_file) for image_file in image_files]
    missing_scenes = [path for path in scene_paths if not path.is_file()]
    if missing_scenes:
        raise FileNotFoundError(f"Scene image was not found: {missing_scenes[0]}")

    audio_clip = None
    video_clip = None
    slides = []

    try:
        audio_clip = AudioFileClip(str(audio_path))
        seconds_per_scene = max(audio_clip.duration / len(scene_paths), 2)

        for scene_path in scene_paths:
            scene_clip = ImageClip(str(scene_path))
            scale = max(width / scene_clip.w, height / scene_clip.h)
            scene_clip = scene_clip.resize(scale).crop(
                x_center=scene_clip.w * scale / 2,
                y_center=scene_clip.h * scale / 2,
                width=width,
                height=height,
            )
            slides.append(scene_clip.set_duration(seconds_per_scene))

        video_clip = concatenate_videoclips(slides, method="compose").set_audio(audio_clip)
        video_clip.write_videofile(
            str(destination),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
    finally:
        if video_clip is not None:
            video_clip.close()
        for slide in slides:
            slide.close()
        if audio_clip is not None:
            audio_clip.close()

    return destination
