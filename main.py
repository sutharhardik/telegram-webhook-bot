from flask import Flask, request
import requests, os, json, threading, time, datetime

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
DEV_CHAT_ID = os.environ.get("DEV_CHAT_ID")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
CHAT_FILE = "chat_id.txt"
LOG_FILE = "logfile.txt"


# ------------------------ Logging (Render safe) ------------------------
def log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(str(msg) + "\n")
    except:
        pass


# ------------------------ Telegram Sender ------------------------
def send_msg(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        log(f"SEND ERROR: {e}")


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


# ------------------------ AI Generator (DeepSeek) ------------------------
def ai_generate_reply(user_text, mode="reply"):

    if mode == "reply":
        prompt = f"""
You are Hardik replying to his fiancée.

Style:
- Gujarati + Hinglish mix
- Romantic, flirty, teasing, cute
- Natural and emotional, not robotic
- Max 25 words

Her message:
{user_text}

Reply exactly like Hardik.
"""

    elif mode == "daily_joke":
        prompt = """
Write a Gujarati/Hinglish cute, romantic, teasing daily note.
Short, sweet, flirty.
Max 2 lines.
"""

    elif mode == "special":
        prompt = """
Write a powerful romantic Gujarati/Hinglish love message.
Very emotional, warm, heart-melting.
Max 25 words.
"""

    try:
        res = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_KEY}"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 80,
                "temperature": 0.9
            }
        ).json()

        # Debug log
        log(json.dumps(res))

        if "choices" in res:
            return res["choices"][0]["message"]["content"].strip()

        if "error" in res:
            log("AI ERROR: " + str(res["error"]))
            return "Aww baby… thodu error aayu, pan tu perfect lage che ❤️"

        return "Aww baby… tu bas cute lage che ❤️"

    except Exception as e:
        log(f"AI FATAL ERROR: {e}")
        return "Aww tu to bas perfect lage che ❤️"


# ------------------------ Daily Scheduler (10:00 AM) ------------------------
def ai_daily_scheduler():
    while True:
        try:
            chat_id = get_user_chat_id()
            if chat_id:
                now = datetime.datetime.now()

                # 10:00 AM message
                if now.hour == 10 and now.minute == 0:
                    msg = ai_generate_reply("", mode="daily_joke")
                    send_msg(chat_id, f"🌞 Good Morning Baby!\n\n{msg}")
                    time.sleep(60)

            time.sleep(20)

        except Exception as e:
            log(f"SCHEDULER ERROR: {e}")
            time.sleep(30)


threading.Thread(target=ai_daily_scheduler, daemon=True).start()


# ------------------------ Webhook ------------------------
@app.route("/", methods=["GET"])
def home():
    return "💕 AI Love Bot Running"


@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        log("INCOMING: " + json.dumps(data))

        if "message" not in data:
            return "OK"

        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        save_user_chat_id(chat_id)

        # Forward to developer
        if DEV_CHAT_ID:
            send_msg(DEV_CHAT_ID, f"Her: {text}")

        # LOVE triggers
        if any(x in text.lower() for x in ["love you", "miss you", "😘", "❤️"]):
            reply = ai_generate_reply(text, mode="special")
            send_msg(chat_id, reply)
            return "OK"

        # Normal AI reply
        reply = ai_generate_reply(text, mode="reply")
        send_msg(chat_id, reply)

    except Exception as e:
        log(f"WEBHOOK ERROR: {e}")

    return "OK"


# ------------------------ Flask Runner ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
