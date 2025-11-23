from flask import Flask, request
import requests, os, json, threading, time, random, datetime

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
DEV_CHAT_ID = os.environ.get("DEV_CHAT_ID")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
CHAT_FILE = "chat_id.txt"


# ------------------------ Send Telegram Message ------------------------
def send_msg(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        pass


def get_user_chat_id():
    try:
        if os.path.exists(CHAT_FILE):
            return open(CHAT_FILE).read().strip()
    except:
        pass
    return None


def save_user_chat_id(chat_id):
    try:
        with open(CHAT_FILE, "w") as f:
            f.write(str(chat_id))
    except:
        pass


# ------------------------ AI Generator with TELEGRAM DEBUGGING ------------------------
def ai_generate_reply(user_text, mode="reply"):

    # Build prompt
    if mode == "reply":
        prompt = f"""
You are Hardik replying to his fiancée in Gujarati/Hinglish.
Flirty, romantic, sweet, teasing. Under 25 words.

Her message: "{user_text}"
"""

    elif mode == "daily_joke":
        prompt = """
Give one Gujarati/Hinglish short romantic or flirty cute joke under 20 words.
"""

    elif mode == "special":
        prompt = """
Write an emotional Gujarati/Hinglish romantic message under 25 words.
"""

    # Check API key
    if not OPENAI_KEY:
        send_msg(DEV_CHAT_ID, "💥 ERROR: Missing OPENAI_API_KEY on Render")
        return "Aww… tu mara mate hamesha special j cho ❤️"

    try:
        # Make API call
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_KEY}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 120,
                "temperature": 1.0
            },
            timeout=20
        )

        # Parse raw response
        raw = response.text
        status = response.status_code

        # If NOT success
        if status != 200:
            send_msg(DEV_CHAT_ID,
                     f"🔥 AI ERROR\nSTATUS={status}\nRAW={raw}")
            return "Aww baby… thodu error aayu, pan tu perfect lage che ❤️"

        data = response.json()

        # If OpenAI returns an error JSON
        if "error" in data:
            send_msg(DEV_CHAT_ID,
                     f"🔥 OPENAI ERROR BLOCK:\n{json.dumps(data['error'], indent=2)}")
            return "Aww baby… thodu error aayu, pan tu perfect lage che ❤️"

        # Success
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        # ANY exception → send to you on Telegram
        send_msg(DEV_CHAT_ID, f"🔥 EXCEPTION:\n{str(e)}")
        return "Aww tu to bas perfect lage che ❤️"


# ------------------------ Daily Joke Scheduler ------------------------
def ai_daily_scheduler():
    while True:
        try:
            chat_id = get_user_chat_id()
            if chat_id:
                now = datetime.datetime.now()

                if now.hour == 10 and now.minute == 0:
                    joke = ai_generate_reply("", mode="daily_joke")
                    send_msg(chat_id, f"🌞 Daily Message:\n\n{joke}")
                    time.sleep(60)

            time.sleep(20)
        except Exception as e:
            send_msg(DEV_CHAT_ID, f"🔥 Scheduler Error:\n{str(e)}")
            time.sleep(30)


threading.Thread(target=ai_daily_scheduler, daemon=True).start()


# ------------------------ Webhook ------------------------
@app.route("/", methods=["GET"])
def home():
    return "AI Companion Bot Running", 200


@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json

        if "message" not in data:
            return "OK", 200

        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        save_user_chat_id(chat_id)

        # Notify you with raw message
        if DEV_CHAT_ID:
            send_msg(DEV_CHAT_ID, f"💌 Her: {text}")

        # Romantic triggers
        if "love you" in text.lower() or "miss you" in text.lower():
            reply = ai_generate_reply(text, mode="special")
            send_msg(chat_id, reply)
            return "OK", 200

        # Normal AI reply
        reply = ai_generate_reply(text, mode="reply")
        send_msg(chat_id, reply)

    except Exception as e:
        send_msg(DEV_CHAT_ID, f"🔥 Webhook Error:\n{str(e)}")

    return "OK", 200


# ------------------------ Run Flask ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
