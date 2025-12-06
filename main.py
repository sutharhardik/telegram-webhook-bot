from flask import Flask, request
import requests, os, threading, time, datetime, sys

app = Flask(__name__)

# ---------------------------------------------------------
# ENVIRONMENT VARIABLES
# ---------------------------------------------------------
TOKEN = os.environ.get("BOT_TOKEN")
DEV_CHAT_ID = os.environ.get("DEV_CHAT_ID")
GROQ_KEY = os.environ.get("GROQ_API_KEY")
PORT = int(os.environ.get("PORT", 5000))

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# Render-safe persistent paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_FILE = os.path.join(BASE_DIR, "chat_id.txt")
LAST_SENT_FILE = os.path.join(BASE_DIR, "last_sent.txt")


# ---------------------------------------------------------
# LOGGING (Render-compatible)
# ---------------------------------------------------------
def log(msg):
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


# ---------------------------------------------------------
# TELEGRAM SEND
# ---------------------------------------------------------
def send_msg(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except Exception as e:
        log(f"SEND ERROR: {e}")


# ---------------------------------------------------------
# CHAT ID PERSISTENCE (ROBUST)
# ---------------------------------------------------------
def save_chat_id(chat_id):
    try:
        with open(CHAT_FILE, "w") as f:
            f.write(str(chat_id))
            f.flush()
            os.fsync(f.fileno())
        log(f"CHAT ID SAVED: {chat_id}")
    except Exception as e:
        log(f"CHAT SAVE ERROR: {e}")


def get_chat_id():
    try:
        if os.path.exists(CHAT_FILE):
            return open(CHAT_FILE).read().strip()
    except Exception as e:
        log(f"CHAT READ ERROR: {e}")
    return None


# ---------------------------------------------------------
# GROQ AI
# ---------------------------------------------------------
def ai_generate(prompt_text):
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.95,
                "max_tokens": 150,
            },
            timeout=15
        ).json()

        return res["choices"][0]["message"]["content"].strip()

    except Exception as e:
        log(f"GROQ ERROR: {e}")
        return "Aaj thoda shy ho gaya baby… but I still miss you ❤️"


# ---------------------------------------------------------
# PROMPTS
# ---------------------------------------------------------
def build_reply_prompt(text):
    return f"""
You are texting your fiancée.

Tone:
- Hindi + English mix
- Flirty, romantic, teasing
- Adult-clean (double meaning ok, no vulgar words)
- Max 25 words

Her message:
{text}

Reply:
"""


# ---------------------------------------------------------
# ✅ BULLETPROOF DAILY SCHEDULER
# ---------------------------------------------------------
def scheduler():
    log("SCHEDULER STARTED")

    while True:
        try:
            cid = get_chat_id()
            now = datetime.datetime.now()
            today = now.strftime("%Y-%m-%d")

            last_sent = None
            if os.path.exists(LAST_SENT_FILE):
                last_sent = open(LAST_SENT_FILE).read().strip()

            # Fire ONCE per day, after 10 AM
            if cid and now.hour >= 10 and last_sent != today:

                prompt = """
Hindi + English romantic message.
Boyfriend vibe.
Flirty, playful, adult-clean.
Morning affection or naughty hint.
Max 35 words.
"""

                msg = ai_generate(prompt)
                send_msg(cid, f"🌞 Good Morning Baby ❤️\n\n{msg}")

                with open(LAST_SENT_FILE, "w") as f:
                    f.write(today)

                log(f"DAILY MESSAGE SENT: {today}")

            time.sleep(30)

        except Exception as e:
            log(f"SCHEDULER ERROR: {e}")
            time.sleep(60)


threading.Thread(target=scheduler, daemon=True).start()


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "Telegram Love Bot running ❤️", 200


@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        log(f"WEBHOOK: {data}")

        msg = data.get("message")
        if not msg:
            return "OK", 200

        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        save_chat_id(chat_id)

        if DEV_CHAT_ID:
            send_msg(DEV_CHAT_ID, f"Her: {text}")

        prompt = build_reply_prompt(text)
        reply = ai_generate(prompt)
        send_msg(chat_id, reply)

    except Exception as e:
        log(f"WEBHOOK ERROR: {e}")

    return "OK", 200


# ---------------------------------------------------------
# SERVER
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
