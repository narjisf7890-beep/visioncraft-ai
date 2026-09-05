# VisionCraft AI

VisionCraft AI is a web app that generates images from text prompts. Users can sign up, generate free "Standard" quality images (limited per day), or upgrade to "Premium" for higher quality prints using credits.

## ✨ Features

- User accounts (signup, login, logout)
- Forgot password / reset password via email
- Standard tier — free, limited to 5 images per day
- Premium tier — credit-based, higher quality images (1 free credit on signup)
- Payment via Safepay (currently in sandbox/test mode)
- Prompt history ("Contact Sheet") saved per user
- Admin dashboard to view total users, Pro members, and estimated revenue

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite (via Flask-SQLAlchemy) |
| Auth | Flask-Login |
| Email | Flask-Mail |
| Frontend | HTML, CSS, JavaScript (Vanilla) |
| Image Generation | Pollinations.ai (free tier), Replicate (FLUX Dev, optional upgrade) |
| Payments | Safepay (Pakistan) |

## 📁 Project Structure

```
visioncraft-web/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── static/
│   ├── style.css
│   ├── script.js
│   └── generated_images/   # Generated image outputs
└── templates/
    ├── index.html          # Main app page
    ├── login.html
    ├── signup.html
    ├── forgot_password.html
    ├── reset_password.html
    ├── upgrade.html
    └── admin.html          # Admin dashboard
```

## 🚀 Running Locally

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Create a `.env` file with the following variables:
   ```
   SECRET_KEY=your-secret-key
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   POLLINATIONS_KEY=your-pollinations-key (optional)
   REPLICATE_API_TOKEN=your-replicate-token (optional, enables higher quality Premium images)
   ```
3. Run the app:
   ```
   python app.py
   ```
4. Open `http://127.0.0.1:5000` in your browser.

## 📌 Notes

- Payments are currently processed through a Safepay **sandbox (test mode)** account. Switch to a live Safepay account before accepting real payments.
- Premium image generation uses Pollinations by default. Adding a `REPLICATE_API_TOKEN` automatically switches Premium generation to Replicate's FLUX Dev model for better quality.