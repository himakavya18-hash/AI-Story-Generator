from uuid import uuid4

from flask import Flask, redirect, render_template, request, url_for

from utils.ai_utils import ask_ai
from utils.scene_image_utils import create_story_scene_images
from utils.storage_utils import (
    get_stories,
    get_tts_rate,
    initialize_database,
    save_story,
    set_tts_rate,
    toggle_favorite,
)
from utils.tts_utils import text_to_speech
from utils.ttv_utils import images_to_video

app = Flask(__name__)
initialize_database()

@app.route("/", methods=["GET", "POST"])
def home():
    prompt = ""
    story = None
    error = None
    audio_url = None
    audio_error = None
    video_url = None
    video_error = None

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()

        if not prompt:
            error = "Please enter a story prompt first."
        else:
            story = ask_ai(prompt)
            if story.startswith("Error:"):
                error = story
                story = None
            else:
                try:
                    story_id = uuid4().hex
                    audio_path = text_to_speech(
                        story, f"static/audio/story-{story_id}.wav", rate=get_tts_rate()
                    )
                    audio_url = url_for(
                        "static",
                        filename=audio_path.relative_to("static").as_posix(),
                    )
                except Exception as exc:
                    audio_error = f"The story was generated, but audio could not be created: {exc}"
                else:
                    try:
                        scene_images = create_story_scene_images(
                            story,
                            f"static/scenes/{story_id}",
                        )
                        video_path = images_to_video(
                            scene_images,
                            audio_path,
                            f"static/video/story-{story_id}.mp4",
                        )
                        video_url = url_for(
                            "static",
                            filename=video_path.relative_to("static").as_posix(),
                        )
                    except Exception as exc:
                        video_error = (
                            "The story and audio were generated, but video could not be created: "
                            f"{exc}"
                        )

                save_story(prompt, story, audio_url, video_url)

    return render_template(
        "index.html",
        prompt=prompt,
        story=story,
        error=error,
        audio_url=audio_url,
        audio_error=audio_error,
        video_url=video_url,
        video_error=video_error,
        stories=get_stories(limit=10),
        page="home",
        tts_rate=get_tts_rate(),
    )


@app.get("/history")
def history():
    return render_template(
        "index.html",
        page="history",
        stories=get_stories(),
        tts_rate=get_tts_rate(),
    )


@app.get("/favorites")
def favorites():
    return render_template(
        "index.html",
        page="favorites",
        stories=get_stories(favorites_only=True),
        tts_rate=get_tts_rate(),
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    setting_error = None
    if request.method == "POST":
        try:
            set_tts_rate(int(request.form.get("tts_rate", "")))
            return redirect(url_for("settings"))
        except (TypeError, ValueError):
            setting_error = "Narration speed must be a number between 100 and 250."

    return render_template(
        "index.html",
        page="settings",
        stories=[],
        tts_rate=get_tts_rate(),
        setting_error=setting_error,
    )


@app.post("/stories/<int:story_id>/favorite")
def change_favorite(story_id: int):
    toggle_favorite(story_id)
    destination = request.form.get("next_page", "history")
    allowed_destinations = {"home": "home", "history": "history", "favorites": "favorites"}
    return redirect(url_for(allowed_destinations.get(destination, "history")))

if __name__ == "__main__":
    app.run(debug=True)
