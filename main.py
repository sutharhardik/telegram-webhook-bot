from flask import Flask, request
import requests, os, json, datetime

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
MY_CHAT_ID = os.environ.get("DEV_CHAT_ID")  # Your chat ID
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

def send_msg(chat_id, text):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print("Send error:", e)

@app.route("/", methods=["GET"])
def home():
    return "Telegram Webhook Running!"

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("Incoming:", data)

    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # Save user chat_id
        with open("chat_id.txt", "w") as f:
            f.write(str(chat_id))

        # Notify developer
        if MY_CHAT_ID:
            send_msg(MY_CHAT_ID, f"User connected. Chat ID: {chat_id}")

        # Auto replies to your fiancée
        replies = ["Hehe 🤭", "Awwww 😄", "Tell me more ❤️", "You’re cute ✨"]
        auto = replies[len(text) % len(replies)]
        send_msg(chat_id, auto)

    return "OK", 200

# 🔥 THIS WAS MISSING — Render needs this to start the server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
