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
# GROQ AI GENERATOR
# ---------------------------------------------------------
def ai_generate(prompt_text):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_KEY}"
        }

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt_text}],
            "max_tokens": 150,
            "temperature": 0.95,
        }

        res = requests.post(url, headers=headers, json=payload).json()

        if "error" in res:
            log(f"GROQ ERROR: {res['error']}")
            return "Baby thoda error aaya… par tu phir bhi cutest ho ❤️"

        return res["choices"][0]["message"]["content"].strip()

    except Exception as e:
        log(f"GROQ EXCEPTION: {e}")
        return "Aww baby cute ho tum ❤️"



# ---------------------------------------------------------
# BUILD PROMPT — NORMAL REPLY (FLIRTY + ADULT-CLEAN)
# ---------------------------------------------------------
def build_reply_prompt(text):
    return f"""
You are Hardik texting his fiancée.

Tone:
- Hindi + English only
- Boyfriend style
- Flirty, teasing, romantic
- Light adult vibe allowed but CLEAN (no explicit words)
- Bold compliments, naughty hints, double meaning OK
- Max 20–25 words

Her message:
{text}

Generate reply:
"""


# ---------------------------------------------------------
# DAILY SCHEDULER — ADULT CLEAN JOKES + FLIRTY LINES
# ---------------------------------------------------------
def scheduler():
    while True:
        try:
            cid = get_chat_id()
            now = datetime.datetime.now()

            if cid and now.hour == 10 and now.minute == 0:

                prompt = """
- Hindi + English mix
- Deeply romantic, flirty, playful
- Adult-clean: Double meaning allowed, seductive vibe okay, but NO vulgar or explicit words
- Should feel like a cute, naughty, loving boyfriend teasing his girlfriend
- Emotion-rich, warm, intimate, fun
- High creativity
- Can be a morning wish, a naughty hint, or a playful adult joke
- Use poetic, emotional, or teasing style
- Max 35 words
"""

                msg = ai_generate(prompt)
                send_msg(cid, f"🌞 Good Morning Baby ❤️\n\n{msg}")
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
# WEBHOOK — MAIN AI LOGIC
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

        # Mirror to dev
        if DEV_CHAT_ID:
            send_msg(DEV_CHAT_ID, f"Her: {text}")

        # Romantic triggers
        if any(x in text.lower() for x in ["love you", "miss you", "❤️", "😘", "😍"]):
            romantic_prompt = """
Generate a short romantic Hindi-English line.
Tone:
- Deep, emotional, warm
- Boyfriend style
- Max 20–25 words
"""
            reply = ai_generate(romantic_prompt)
            send_msg(chat_id, reply)
            return "OK", 200

        # Normal flirty reply
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
