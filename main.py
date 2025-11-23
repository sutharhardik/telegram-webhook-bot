from flask import Flask, request
import requests, os, json, threading, time, random, datetime

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
DEV_CHAT_ID = os.environ.get("DEV_CHAT_ID")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
CHAT_FILE = "chat_id.txt"


# ------------------------ Basic Telegram Sender ------------------------
def send_msg(chat_id, text):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage",
                      json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print("Send error:", e)


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


# ------------------------ AI Generator (Heart of the System) ------------------------
def ai_generate_reply(user_text, mode="reply"):
    """
    mode = reply | daily_joke | special
    """

    if mode == "reply":
        prompt = f"""
You are Hardik replying to his fiancée.

Language style:
- Gujarati + Hinglish mix
- Cute, romantic, teasing, flirty
- Personal tone, NO robotic words
- Keep it emotional, natural, warm
- If she flirts, flirt back playfully
- If she is angry, reply soft and caring
- If she sends normal text, reply sweetly
- MAX 25 words

Her message:
"{user_text}"

Reply exactly like Hardik would.
"""

    elif mode == "daily_joke":
        prompt = """
Create one Gujarati/Hinglish sweet/flirty romantic joke or lovable teasing message.
Style:
- Very cute
- Short
- Playful
- Feels like interest/love
- 1–2 lines MAX
"""

    elif mode == "special":
        prompt = """
Generate a very romantic Gujarati/Hinglish surprise message that feels emotional, loving, warm.
Something that would melt her heart.
Keep it under 25 words.
"""

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_KEY}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 80,
                "temperature": 1.0
            }
        ).json()

        return r["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("AI ERROR:", e)
        return "Aww tu to bas perfect lage che ❤️"


# ------------------------ AI Daily Joke Scheduler ------------------------
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
            print("Scheduler error:", e)
            time.sleep(30)


threading.Thread(target=ai_daily_scheduler, daemon=True).start()


# ------------------------ Webhook: Uses Full AI Mode ------------------------
@app.route("/", methods=["GET"])
def home():
    return "AI Companion Bot Running", 200


@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("Incoming:", data)

        if "message" not in data:
            return "OK", 200

        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        save_user_chat_id(chat_id)

        # Notify dev (you)
        if DEV_CHAT_ID:
            send_msg(DEV_CHAT_ID, f"Her: {text}")

        # Special emotional phrase trigger
        if "love you" in text.lower() or "miss you" in text.lower():
            reply = ai_generate_reply(text, mode="special")
            send_msg(chat_id, reply)
            return "OK", 200

        # Normal AI reply for every message
        reply = ai_generate_reply(text, mode="reply")
        send_msg(chat_id, reply)

    except Exception as e:
        print("Webhook error:", e)

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
