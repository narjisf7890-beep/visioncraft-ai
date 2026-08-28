"""
app.py

Flask backend for VisionCraft AI (web version).
Serves the front-end page and exposes an endpoint that generates
images by calling the Pollinations.ai text-to-image API.
"""

import os
import shutil
from datetime import datetime
from urllib.parse import quote

import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from gradio_client import Client, handle_file

app = Flask(__name__)

API_BASE_URL = "https://image.pollinations.ai/prompt"
GENERATED_FOLDER = os.path.join(app.static_folder, "generated_images")
VIDEO_FOLDER = os.path.join(app.static_folder, "generated_videos")
REQUEST_TIMEOUT_SECONDS = 60

# The Hugging Face Space that turns a still image into a short video.
VIDEO_SPACE_NAME = "kulkas2pintu/wan555"

os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# The gradio_client connects once when the server starts, not on every request.
_video_client = None


def _get_video_client():
    """Lazily connects to the Hugging Face Space (only on first use)."""
    global _video_client
    if _video_client is None:
        _video_client = Client(VIDEO_SPACE_NAME)
    return _video_client


def _generate_image_file(prompt: str) -> str:
    """Calls Pollinations.ai and returns the local path of the saved image."""
    encoded_prompt = quote(prompt)
    api_url = f"{API_BASE_URL}/{encoded_prompt}"

    response = requests.get(api_url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"image_{timestamp}.png"
    filepath = os.path.join(GENERATED_FOLDER, filename)

    with open(filepath, "wb") as image_file:
        image_file.write(response.content)

    return filepath


def _extract_video_path(result):
    """
    The Space can return its result in a few different shapes
    depending on its version, so we check the common ones.
    """
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("video", "name", "path"):
            value = result.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, dict) and value.get("video"):
                return value["video"]
    if isinstance(result, (list, tuple)):
        for item in result:
            path = _extract_video_path(item)
            if path:
                return path
    return None


@app.route("/")
def index():
    """Renders the main page."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Receives a prompt from the front-end, requests an image from the
    API, saves it, and returns its URL as JSON.
    """
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "Please describe an image first."}), 400

    try:
        filepath = _generate_image_file(prompt)
    except requests.exceptions.RequestException as error:
        return jsonify({"error": f"Could not generate image: {error}"}), 502

    filename = os.path.basename(filepath)
    return jsonify({
        "image_url": f"/static/generated_images/{filename}",
        "prompt": prompt,
    })


@app.route("/generate-video", methods=["POST"])
def generate_video():
    """
    Generates a still image from the prompt, then sends that image to
    the Hugging Face Space to be animated into a short video.
    """
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "Please describe a video first."}), 400

    # Step 1: create the starting image
    try:
        image_path = _generate_image_file(prompt)
    except requests.exceptions.RequestException as error:
        return jsonify({"error": f"Could not create the source image: {error}"}), 502

    # Step 2: animate that image using the Hugging Face Space
    try:
        client = _get_video_client()
        result = client.predict(
            input_image=handle_file(image_path),
            last_image=handle_file(image_path),
            prompt=prompt,
            steps=4,
            negative_prompt=(
                "blurry, low quality, static, distorted, deformed, "
                "extra limbs, bad anatomy, watermark, text"
            ),
            duration_seconds=3.5,
            guidance_scale=1,
            guidance_scale_2=1,
            seed=42,
            randomize_seed=True,
            quality=6,
            scheduler="UniPCMultistep",
            flow_shift=3,
            frame_multiplier=16,
            video_component=True,
            safe_mode=True,
            api_name="/generate_video",
        )
    except Exception as error:
        return jsonify({"error": f"Video generation failed: {error}"}), 502

    source_video_path = _extract_video_path(result)
    if not source_video_path or not os.path.exists(source_video_path):
        return jsonify({"error": "The video service did not return a valid file."}), 502

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"video_{timestamp}.mp4"
    dest_path = os.path.join(VIDEO_FOLDER, filename)
    shutil.copy(source_video_path, dest_path)

    return jsonify({
        "video_url": f"/static/generated_videos/{filename}",
        "prompt": prompt,
    })


@app.route("/gallery")
def gallery():
    """Returns a list of previously generated images, most recent first."""
    files = sorted(os.listdir(GENERATED_FOLDER), reverse=True)
    urls = [f"/static/generated_images/{f}" for f in files if f.endswith(".png")]
    return jsonify(urls[:12])


if __name__ == "__main__":
    app.run(debug=True, port=5000)