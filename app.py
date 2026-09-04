"""
app.py

Flask backend for VisionCraft AI.
Adds user accounts (signup/login), a daily free limit on Standard images,
and a Premium tier that uses credits (1 free credit on signup, more via
a paid package) and requires being logged in and having credits available.
"""

import os
import json
import time
from datetime import datetime, timedelta
from urllib.parse import quote
import re
from itsdangerous import URLSafeTimedSerializer
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import secrets
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-change-in-production"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///visioncraft.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

GENERATED_FOLDER = os.path.join(app.static_folder, "generated_images")
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"
POLLINATIONS_KEY = os.environ.get("POLLINATIONS_KEY")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
REQUEST_TIMEOUT_SECONDS = 60
DAILY_FREE_LIMIT = 5
ADMIN_EMAIL = "narjisf7890@gmail.com"

os.makedirs(GENERATED_FOLDER, exist_ok=True)


# ---- Database model ----
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    subscription = db.Column(db.String(50), default="free")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(64), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    credits = db.Column(db.Integer, default=1)
    standard_images_today = db.Column(db.Integer, default=0)
    standard_images_date = db.Column(db.Date, nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---- Image generation helpers ----
def _save_image_bytes(image_bytes: bytes, prompt: str = "") -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"image_{timestamp}.png"
    filepath = os.path.join(GENERATED_FOLDER, filename)
    with open(filepath, "wb") as image_file:
        image_file.write(image_bytes)

    meta_path = os.path.join(GENERATED_FOLDER, f"image_{timestamp}.json")
    with open(meta_path, "w", encoding="utf-8") as meta_file:
        json.dump({"prompt": prompt}, meta_file)

    return filepath


def _generate_standard(prompt: str) -> str:
    encoded_prompt = quote(prompt)
    url = f"{POLLINATIONS_URL}/{encoded_prompt}"
    headers = {}
    if POLLINATIONS_KEY:
        headers["Authorization"] = f"Bearer {POLLINATIONS_KEY}"

    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return _save_image_bytes(response.content, prompt)
        except Exception as error:
            last_error = error
            time.sleep(2)
    raise last_error


def _generate_premium_replicate(prompt: str) -> str:
    """Uses Replicate's FLUX Dev model. Only runs if REPLICATE_API_TOKEN is set."""
    import replicate
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    output = client.run(
        "black-forest-labs/flux-dev",
        input={"prompt": prompt, "num_outputs": 1}
    )
    image_url = output[0] if isinstance(output, list) else output
    response = requests.get(str(image_url), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return _save_image_bytes(response.content, prompt)


def _generate_premium_pollinations(prompt: str) -> str:
    """Fallback: free Pollinations API, used when no Replicate token is configured."""
    encoded_prompt = quote(prompt)
    url = f"{POLLINATIONS_URL}/{encoded_prompt}?width=512&height=512&nologo=true"
    headers = {}
    if POLLINATIONS_KEY:
        headers["Authorization"] = f"Bearer {POLLINATIONS_KEY}"

    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return _save_image_bytes(response.content, prompt)
        except Exception as error:
            last_error = error
            time.sleep(2)
    raise last_error


def _generate_premium(prompt: str) -> str:
    if REPLICATE_API_TOKEN:
        return _generate_premium_replicate(prompt)
    return _generate_premium_pollinations(prompt)


# ---- Auth routes ----
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Please fill in both fields.")
            return redirect(url_for("signup"))

        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return redirect(url_for("signup"))
        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter.")
            return redirect(url_for("signup"))
        if not re.search(r"[a-z]", password):
            flash("Password must contain at least one lowercase letter.")
            return redirect(url_for("signup"))
        if not re.search(r"[0-9]", password):
            flash("Password must contain at least one number.")
            return redirect(url_for("signup"))
        if not re.search(r"[!@#$%^&*]", password):
            flash("Password must contain at least one special character (!@#$%^&*).")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.")
            return redirect(url_for("signup"))

        user = User(
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Incorrect email or password.")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_hex(16)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            reset_link = f"http://127.0.0.1:5000/reset-password/{token}"

            msg = Message(
                "Password Reset Request",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )
            msg.body = f"""
            Hello,

            Click this link to reset your password:

            {reset_link}

            This link will expire in 1 hour. If you didn't request this, you can safely ignore this email.
            """
            mail.send(msg)

        return "If that email is registered, a password reset link has been sent."

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return "This password reset link is invalid or has expired. Please request a new one."

    if request.method == "POST":
        password = request.form.get("password") or ""

        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return redirect(url_for("reset_password", token=token))

        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter.")
            return redirect(url_for("reset_password", token=token))

        if not re.search(r"[a-z]", password):
            flash("Password must contain at least one lowercase letter.")
            return redirect(url_for("reset_password", token=token))

        if not re.search(r"[0-9]", password):
            flash("Password must contain at least one number.")
            return redirect(url_for("reset_password", token=token))

        if not re.search(r"[!@#$%^&*]", password):
            flash("Password must contain at least one special character (!@#$%^&*).")
            return redirect(url_for("reset_password", token=token))

        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash("Your password has been reset. Please log in.")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/plans")
def plans():
    return render_template("plans.html")


# ---- Premium upgrade (demo checkout, no real payment) ----
@app.route("/upgrade", methods=["GET"])
@login_required
def upgrade():
    return render_template("upgrade.html")


@app.route("/upgrade/confirm", methods=["POST"])
@login_required
def upgrade_confirm():
    # DEMO ONLY: no real payment processor is connected here.
    # In production, this should only run after a verified payment webhook,
    # and should add credits from the specific package purchased.
    current_user.is_premium = True
    current_user.credits += 100
    db.session.commit()
    flash("You're now a Premium member! 100 credits added.")
    return redirect(url_for("index"))


# ---- Admin dashboard ----
@app.route("/admin")
@login_required
def admin():
    if current_user.email != ADMIN_EMAIL:
        return "Access denied.", 403

    all_users = User.query.order_by(User.created_at.desc()).all()
    total_users = len(all_users)
    pro_users = [u for u in all_users if u.is_premium]
    total_pro = len(pro_users)
    estimated_revenue = total_pro * 1500

    return render_template(
        "admin.html",
        users=all_users,
        total_users=total_users,
        total_pro=total_pro,
        estimated_revenue=estimated_revenue,
    )


# ---- Main routes ----
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    tier = (data.get("tier") or "standard").strip()

    if not prompt:
        return jsonify({"error": "Please describe an image first."}), 400

    if tier == "premium":
        if not current_user.is_authenticated:
            return jsonify({"error": "Please log in to use Premium.", "requires_login": True}), 401
        if current_user.credits <= 0:
            return jsonify({"error": "You're out of credits. Please upgrade to buy more.", "requires_upgrade": True}), 402
    else:
        if current_user.is_authenticated:
            today = datetime.utcnow().date()
            if current_user.standard_images_date != today:
                current_user.standard_images_today = 0
                current_user.standard_images_date = today

            if current_user.standard_images_today >= DAILY_FREE_LIMIT:
                return jsonify({
                    "error": f"You've reached your free limit of {DAILY_FREE_LIMIT} images today. Try again tomorrow, or upgrade to Premium."
                }), 429

    try:
        if tier == "premium":
            filepath = _generate_premium(prompt)
        else:
            filepath = _generate_standard(prompt)
    except Exception as error:
        return jsonify({"error": f"Could not generate image: {error}"}), 502

    if tier == "premium":
        current_user.credits -= 1
        db.session.commit()
    elif current_user.is_authenticated:
        current_user.standard_images_today += 1
        db.session.commit()

    filename = os.path.basename(filepath)
    return jsonify({
        "image_url": f"/static/generated_images/{filename}",
        "prompt": prompt,
        "tier": tier,
        "credits_remaining": current_user.credits if (current_user.is_authenticated and tier == "premium") else None,
    })


@app.route("/gallery")
def gallery():
    files = sorted(os.listdir(GENERATED_FOLDER), reverse=True)
    png_files = [f for f in files if f.endswith(".png")]

    results = []
    for f in png_files[:12]:
        prompt_text = "Previous print"
        meta_path = os.path.join(GENERATED_FOLDER, f.replace(".png", ".json"))
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as meta_file:
                    meta = json.load(meta_file)
                    prompt_text = meta.get("prompt") or prompt_text
            except Exception:
                pass
        results.append({
            "url": f"/static/generated_images/{f}",
            "prompt": prompt_text,
        })

    return jsonify(results)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=False)