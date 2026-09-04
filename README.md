# VisionCraft AI

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0-black?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">
</p>

<p align="center">
  <b>Type a thought. Watch it develop.</b><br>
  A text-to-image generator with a chat-style interface, built with Python, Flask, and Google's Gemini API.
</p>

---

## ✨ Overview

VisionCraft AI turns text prompts into AI-generated images through a clean, ChatGPT-style interface. Describe anything, and it "develops" a picture back — no camera required.

Built as an internship project to explore full-stack AI application development: connecting a Python backend to image-generation APIs, and designing a polished, production-style frontend.

## 🖼️ Preview

> *(Add a screenshot or GIF of the app here — this is the first thing visitors see!)*

## 🚀 Features

- **Chat-style interface** — sidebar history + conversational feed, inspired by ChatGPT/Gemini
- **Two quality tiers**
  - **Standard** — free, instant generation via Pollinations.ai
  - **Premium** — higher-quality generation via Google's Gemini image model
- **Contact sheet history** — revisit previously generated images
- **One-click download** of any generated image
- **Responsive design** — works on desktop and mobile
- **Custom "darkroom" visual identity** — dark theme, amber accents, film-inspired animations

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript (vanilla — no framework) |
| Image APIs | Pollinations.ai (free tier), Google Gemini API (premium tier) |
| Deployment | Docker, Hugging Face Spaces |

## 📁 Project Structure

```
visioncraft-web/
├── app.py                    # Flask backend & API routes
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container config for deployment
├── templates/
│   └── index.html            # Main page structure
└── static/
    ├── style.css              # Design system & layout
    ├── script.js               # Frontend interactivity
    └── generated_images/       # Output folder for generated images
```

## ⚙️ Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR-USERNAME/visioncraft-ai.git
   cd visioncraft-ai/visioncraft-web
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. *(Optional, for Premium tier)* Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your_key_here"   # macOS/Linux
   $env:GEMINI_API_KEY="your_key_here"      # Windows PowerShell
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

## 🌐 Live Demo

> *(Add your deployed link here once live, e.g. on Hugging Face Spaces)*

## 🔮 Future Improvements

- User accounts and saved galleries
- Adjustable image size/aspect ratio
- Rate limiting for the Premium tier
- Video generation mode

## 📄 License

This project is open source under the MIT License.

---

<p align="center"><i>Built during an internship to explore practical AI application development.</i></p>