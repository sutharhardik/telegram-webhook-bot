from flask import Flask, request
import requests, os, json, threading, time, datetime, sys

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
DEV_CHAT_ID = os.environ.get("DEV_CHAT_ID")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
CHAT_FILE = "chat_id.txt"


# -----------------------------------
# Utility: log that actually shows in Render
# -----------------------------------
def log(msg):
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


# -----------------------------------
# Telegram sender
# -----------------------------------
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


# -----------------------------------
# DeepSeek AI Generator
# -----------------------------------
def ai_generate(prompt_text):
    """
    Universal AI generator for:
    - reply
    - daily message
    - romantic message
    """
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt_text}],
            "max_tokens": 120,
            "temperature": 0.9,
        }

        res = requests.post(url, headers=headers, json=payload).json()

        if "error" in res:
            log(f"DEEPSEEK ERROR: {res['error']}")
            return "Baby thodu error thayu… pan tu perfect lage che ❤️"

        return res["choices"][0]["message"]["content"].strip()

    except Exception as e:
        log(f"AI EXCEPTION: {e}")
        return "Aww baby cute che tu ❤️"


# -----------------------------------
# Create AI prompt for reply
# -----------------------------------
def build_reply_prompt(text):
    return f"""
You are Hardik texting his fiancée.

Language:
- Gujarati + Hinglish mix
- Soft, romantic, playful
- Reply maximum 20–25 words
- Tone must sound like a real boyfriend, not AI
- If she flirts → flirt cute
- If she is upset → reply calming
- If normal text → reply sweetly

Her message:
{text}

Now generate your reply:
"""


# -----------------------------------
# Daily Message Scheduler
# -----------------------------------
def scheduler():
    while True:
        try:
            cid = get_chat_id()
            if cid:
                now = datetime.datetime.now()

                if now.hour == 10 and now.minute == 0:
                    prompt = """
Give one short Gujarati/Hinglish cute romantic message.
Max 20 words.
Very sweet and loving.
"""
                    msg = ai_generate(prompt)
                    send_msg(cid, f"🌞 Good Morning Message:\n\n{msg}")
                    time.sleep(60)

            time.sleep(20)

        except Exception as e:
            log(f"SCHEDULER ERROR: {e}")
            time.sleep(30)


threading.Thread(target=scheduler, daemon=True).start()


# -----------------------------------
# Flask Home
# -----------------------------------
@app.route("/", methods=["GET"])
def home():
    return "DeepSeek AI Telegram Bot Running", 200


# -----------------------------------
# Webhook Receiver
# -----------------------------------
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

        # Forward to dev (you)
        if DEV_CHAT_ID:
            send_msg(DEV_CHAT_ID, f"Her: {text}")

        # Romantic trigger
        if any(x in text.lower() for x in ["love you", "miss you", "❤️", "😍"]):
            p = """
Create a super romantic Gujarati/Hinglish message,
Max 20 words, emotional and warm.
"""
            send_msg(chat_id, ai_generate(p))
            return "OK", 200

        # Normal conversational reply
        prompt = build_reply_prompt(text)
        reply = ai_generate(prompt)
        send_msg(chat_id, reply)

    except Exception as e:
        log(f"WEBHOOK ERROR: {e}")

    return "OK", 200


# -----------------------------------
# Run App
# -----------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
