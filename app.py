"""
app.py

Flask backend for VisionCraft AI (web version).
Offers two image generation tiers:
  - "standard": free, via Pollinations.ai
  - "premium": paid, via Google's Gemini image model (better quality)
"""

import os
from datetime import datetime
from urllib.parse import quote

import requests
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

GENERATED_FOLDER = os.path.join(app.static_folder, "generated_images")
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"
PREMIUM_MODEL = "gemini-3.1-flash-image-preview"
REQUEST_TIMEOUT_SECONDS = 60

os.makedirs(GENERATED_FOLDER, exist_ok=True)

# The Gemini client connects once when first used, not on every request.
_genai_client = None


def _get_genai_client():
    """Lazily connects to the Gemini API (only on first use)."""
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


def _save_image_bytes(image_bytes: bytes) -> str:
    """Writes image bytes to a uniquely named file and returns its path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"image_{timestamp}.png"
    filepath = os.path.join(GENERATED_FOLDER, filename)

    with open(filepath, "wb") as image_file:
        image_file.write(image_bytes)

    return filepath


def _generate_standard(prompt: str) -> str:
    """Free tier: generates an image using Pollinations.ai."""
    encoded_prompt = quote(prompt)
    url = f"{POLLINATIONS_URL}/{encoded_prompt}"

    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    return _save_image_bytes(response.content)


def _generate_premium(prompt: str) -> str:
    """Paid tier: generates a higher-quality image using Gemini."""
    client = _get_genai_client()

    response = client.models.generate_content(
        model=PREMIUM_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    image_bytes = None
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        raise RuntimeError("The image service did not return an image.")

    return _save_image_bytes(image_bytes)


@app.route("/")
def index():
    """Renders the main page."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Receives a prompt and a tier ("standard" or "premium") from the
    front-end, generates an image accordingly, and returns its URL.
    """
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    tier = (data.get("tier") or "standard").strip()

    if not prompt:
        return jsonify({"error": "Please describe an image first."}), 400

    try:
        if tier == "premium":
            filepath = _generate_premium(prompt)
        else:
            filepath = _generate_standard(prompt)
    except Exception as error:
        return jsonify({"error": f"Could not generate image: {error}"}), 502

    filename = os.path.basename(filepath)
    return jsonify({
        "image_url": f"/static/generated_images/{filename}",
        "prompt": prompt,
        "tier": tier,
    })


@app.route("/gallery")
def gallery():
    """Returns a list of previously generated images, most recent first."""
    files = sorted(os.listdir(GENERATED_FOLDER), reverse=True)
    urls = [f"/static/generated_images/{f}" for f in files if f.endswith(".png")]
    return jsonify(urls[:12])


if __name__ == "__main__":
    app.run(debug=True, port=5000)