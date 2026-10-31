#!/usr/bin/env python3
"""Send Prakom quiz polls to Telegram.

Usage: python3 send_polls.py questions.json
questions.json = list of {"q": str, "options": [str x4], "answer": int (0-based), "explanation": str}
- q must start with "[Nama Modul] N. ..." (<=300 chars), options <=100 chars, explanation <=200 chars.
Sends non-anonymous quiz polls to Yoga's Telegram chat and appends sent questions to asked.txt.
"""
import json, re, sys, time, urllib.request, os, html

DIR = os.path.dirname(os.path.abspath(__file__))
# Token & chat id dibaca dari environment, atau dari ~/.hermes/.env (TELEGRAM_BOT_TOKEN, QUIZ_CHAT_ID)
def _env(name):
    if os.environ.get(name):
        return os.environ[name].strip()
    p = os.path.expanduser(os.environ.get("HERMES_ENV", "~/.hermes/.env"))
    m = re.search(r'^' + name + r'=(.*)$', open(p).read(), re.M) if os.path.exists(p) else None
    return m.group(1).strip().strip('"\'') if m else ""
tok = _env("TELEGRAM_BOT_TOKEN")
CHAT = _env("QUIZ_CHAT_ID") or _env("TELEGRAM_HOME_CHANNEL")

Q = json.load(open(sys.argv[1]))
bad = []
for i, x in enumerate(Q):
    if len(x["q"]) > 300 or len(x["explanation"]) > 200 or len(x["options"]) < 2 \
       or any(len(o) > 100 for o in x["options"]) or not (0 <= x["answer"] < len(x["options"])):
        bad.append(i + 1)
if bad:
    sys.exit(f"Invalid questions (length/answer): {bad}")

def call(method, payload):
    data = json.dumps(payload).encode()
    for _ in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                f"https://api.telegram.org/bot{tok}/{method}", data=data,
                headers={"Content-Type": "application/json"}), timeout=30)
            return json.loads(r.read())
        except Exception as e:
            print("retry:", e); time.sleep(3)
    return {"ok": False}

sent = 0
with open(os.path.join(DIR, "asked.txt"), "a") as log:
    for x in Q:
        res = call("sendPoll", {"chat_id": CHAT, "question": x["q"],
                   "options": [{"text": o} for o in x["options"]], "type": "quiz",
                   "correct_option_id": x["answer"], "explanation": x["explanation"],
                   "is_anonymous": False})
        print(res.get("ok"), x["q"][:50])
        if res.get("ok"):
            sent += 1
            log.write(x["q"] + "\n")
            detail = (x.get("detail") or "").strip()
            if detail:
                head = html.escape(x["q"].split("]")[0] + "]") if x["q"].startswith("[") else ""
                num = re.search(r"\]\s*(\d+)\.", x["q"])
                title = f"📖 Pembahasan soal {num.group(1) if num else ''} {head}".strip()
                text = f"<b>{title}</b>\n<tg-spoiler>{html.escape(detail)[:3800]}</tg-spoiler>"
                d = call("sendMessage", {"chat_id": CHAT, "text": text, "parse_mode": "HTML",
                         "reply_parameters": {"message_id": res["result"]["message_id"]}})
                print("  detail:", d.get("ok"))
        time.sleep(0.6)
print(f"SENT {sent}/{len(Q)}")
