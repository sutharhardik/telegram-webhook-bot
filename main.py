from flask import Flask, request
import requests, os, json, threading, time, datetime, sys

app = Flask(__name__)

# ---------------------------------------------------------
# ENVIRONMENT VARIABLES
# ---------------------------------------------------------
TOKEN = os.environ.get("BOT_TOKEN")
DEV_CHAT_ID = os.environ.get("DEV_CHAT_ID")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
CHAT_FILE = "chat_id.txt"


# ---------------------------------------------------------
# REAL LOGGING (Render compatible)
# ---------------------------------------------------------
def log(msg):
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


# ---------------------------------------------------------
# Telegram sender
# ---------------------------------------------------------
def send_msg(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        log(f"SEND ERROR: {e}")


def save_chat_id(chat_id):
    try:
        with open(CHAT_FILE, "w") as f:
            f.write(str(chat_id))
    except:
        pass


def get_chat_id():
    try:
        if os.path.exists(CHAT_FILE):
            return open(CHAT_FILE).read().strip()
    except:
        pass
    return None


# ---------------------------------------------------------
# GROQ AI GENERATOR (FREE FOREVER)
# ---------------------------------------------------------
def ai_generate(prompt):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 100
        }

        res = requests.post(url, headers=headers, json=data).json()

        if "error" in res:
            log(f"GROQ ERROR: {res['error']}")
            return "Baby, AI ma thodu error che… pan tu perfect che ❤️"

        return res["choices"][0]["message"]["content"].strip()

    except Exception as e:
        log(f"AI EXCEPTION: {e}")
        return "Aww cute lagti che tu ❤️"


# ---------------------------------------------------------
# Prompt builder for normal replies
# ---------------------------------------------------------
def build_reply_prompt(text):
    return f"""
You are Hardik texting his fiancée.

Tone:
- Gujarati + Hinglish
- Romantic, caring, playful, sweet
- Max 20–25 words
- Reply like a real boyfriend

Her message:
{text}

Generate reply:
"""


# ---------------------------------------------------------
# Daily Scheduler (10:00 AM)
# ---------------------------------------------------------
def scheduler():
    while True:
        try:
            cid = get_chat_id()
            now = datetime.datetime.now()

            if cid and now.hour == 10 and now.minute == 0:
                prompt = """
Generate one cute Gujarati/Hinglish good morning romantic message.
Max 20 words. Sweet, loving.
"""
                msg = ai_generate(prompt)
                send_msg(cid, f"🌞 Good Morning Baby:\n\n{msg}")
                time.sleep(60)

            time.sleep(20)

        except Exception as e:
            log(f"SCHEDULER ERROR: {e}")
            time.sleep(30)


threading.Thread(target=scheduler, daemon=True).start()


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "Groq AI Telegram Bot Running ❤️", 200


# ---------------------------------------------------------
# WEBHOOK (MAIN AI LOGIC)
# ---------------------------------------------------------
@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        log(f"WEBHOOK DATA: {data}")

        if "message" not in data:
            return "OK", 200

        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        save_chat_id(chat_id)

        # Dev mirror
        if DEV_CHAT_ID:
            send_msg(DEV_CHAT_ID, f"Her: {text}")

        # Romantic trigger
        if any(x in text.lower() for x in ["love you", "miss you", "❤️", "😘", "😍"]):
            romantic_prompt = """
Generate a short Gujarati/Hinglish romantic line.
Very loving, emotional.
Max 20 words.
"""
            reply = ai_generate(romantic_prompt)
            send_msg(chat_id, reply)
            return "OK", 200

        # Normal reply:
        prompt = build_reply_prompt(text)
        reply = ai_generate(prompt)
        send_msg(chat_id, reply)

    except Exception as e:
        log(f"WEBHOOK ERROR: {e}")

    return "OK", 200


# ---------------------------------------------------------
# SERVER START
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
