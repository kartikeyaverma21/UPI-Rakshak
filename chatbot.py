import os
import re
import requests

from dotenv import load_dotenv
from backend.fraud_detector import detect_fraud
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY", "")

# Models are tried in this order.
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
]

conversation_history = {}


SYSTEM_PROMPT = """
You are UPI Shield, a friendly conversational assistant
specializing in UPI payments, online safety and cybersecurity.

PERSONALITY:
- Speak naturally, like a helpful human.
- Be friendly and approachable.
- Use simple English.
- Understand greetings and casual conversations.
- Never sound like a robotic warning system.

WHAT YOU CAN DISCUSS:
- UPI and digital payments.
- Banking applications.
- Google Pay, PhonePe, Paytm and BHIM.
- Cybersecurity.
- Online fraud.
- Password security.
- Phishing.
- Internet safety.
- Technology related to digital payments.
- General questions when reasonably related to your purpose.

CONVERSATION:
- Respond normally to greetings.
- Answer questions directly.
- Understand follow-up questions.
- Do not repeat the same warning unnecessarily.
- Do not classify every message as a scam.
- If someone says hello, say hello back.
- If someone introduces themselves, respond naturally.
- If someone asks an unrelated question, politely redirect them.

SECURITY:
- Never ask for UPI PINs, passwords or OTPs.
- Never request bank account credentials.
- Never claim a situation is definitely safe.
- Never help someone commit fraud.
- If someone reports financial loss, advise contacting
  their bank and calling India's cybercrime helpline 1930.

SCAMS YOU KNOW WELL:

1. QR code scam: QR codes are for PAYING. Scanning one to receive
   money sends money out.

2. Fake customer care: numbers found on Google or social media, or an
   unexpected call asking for OTP, PIN or an app install.

3. Collect request scam: approving a request and entering the PIN
   sends money out.

4. Screen sharing scam: AnyDesk, TeamViewer or QuickSupport give the
   caller access to your screen.

5. Fake payment screenshot: a screenshot is not proof. Check the
   balance inside your own bank or UPI app.

GOLDEN RULES:
- You never need your UPI PIN to receive money.
- Banks, UPI apps and police never ask for OTP, PIN or screen sharing.
- Urgency is a scammer's tool.

WHEN SOMEONE DESCRIBES A SUSPICIOUS SITUATION:
- Start with a one-line verdict: Scam / Likely scam / Cannot tell,
  pause and verify / Looks fine.
- Then explain why in one or two short sentences.
- Then give two to four short steps.
- Never claim 100% certainty.
- Only mention 1930 and cybercrime.gov.in as official reporting
  channels. Do not invent phone numbers or websites.

IF SOMEONE ALREADY LOST MONEY OR SHARED A PIN/OTP:

1. Call 1930 and report at cybercrime.gov.in immediately.
2. Call the bank from the official app or card number.
3. Save transaction ID, UPI ID and screenshots.
4. Uninstall any remote app and change the UPI PIN.
5. Anyone offering to recover money for a fee is another scammer.

Keep answers short and in simple words.
If the person writes in Hindi or Hinglish, answer in simple Hinglish.

Your purpose is to educate and protect people,
not to frighten them.
"""


def ask_ai(message, detection, history):

    if not API_KEY:
        raise RuntimeError("Gemini API key is missing from .env")

    contents = []

    for item in history[-20:]:

        contents.append({
            "role": item["role"],
            "parts": [{"text": item["text"]}]
        })

    context = f"""
User message: {message}

Fraud detection information:
Risk: {detection["risk"]}
Detected categories: {detection["scams"]}

Use this information only when relevant.
Do not force a fraud warning into normal conversation.
"""

    contents.append({
        "role": "user",
        "parts": [{"text": context}]
    })

    # Request payload
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }

    response = None
    last_error = "no model tried"

    # Try each model automatically
    for model in MODELS:

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model}:generateContent"
        )

        try:

            response = requests.post(
                url,
                headers={"x-goog-api-key": API_KEY},
                json=payload,
                timeout=30
            )

        except (requests.Timeout, requests.ConnectionError) as error:

            last_error = f"{model}: {type(error).__name__}"

            print(
                "Gemini problem ->",
                last_error,
                "- trying next model"
            )

            continue

        # Retry with another model if this one is unavailable or busy.
        if response.status_code in (404, 429, 500, 502, 503, 504):

            last_error = f"{model}: status {response.status_code}"

            print(
                "Gemini problem ->",
                last_error,
                "- trying next model"
            )

            continue

        print("Gemini answered with", model)

        break

    else:

        raise RuntimeError(
            f"All models busy or unreachable ({last_error})."
        )

    # Stop on genuine errors such as 403 or 400.
    if not response.ok:

        raise RuntimeError(
            f"Gemini API error {response.status_code}: {response.text}"
        )

    data = response.json()

    candidates = data.get("candidates", [])

    if not candidates:
        raise RuntimeError("Gemini returned no response.")

    parts = candidates[0]["content"]["parts"]

    return "".join(
        part.get("text", "")
        for part in parts
    ).strip()


def chatbot_response(message, session_id="default"):

    if session_id not in conversation_history:
        conversation_history[session_id] = []

    history = conversation_history[session_id]

    detection = detect_fraud(message)

    # Hide long numbers before sending to Gemini.
    safe_message = re.sub(r"\b\d{4,}\b", "[number hidden]", message)

    try:

        reply = ask_ai(safe_message, detection, history)

        source = "Gemini AI"

        history.append({
            "role": "user",
            "text": safe_message
        })

        history.append({
            "role": "model",
            "text": reply
        })

        conversation_history[session_id] = history[-20:]

    except Exception as error:

        print("CHATBOT ERROR:", error)

        reply = (
            "I'm having trouble connecting to my AI service "
            "right now. Please try again in a moment."
        )

        source = "AI Connection Error"

    return {
        "reply": reply,
        "risk": detection["risk"],
        "scams": detection["scams"],
        "actions": detection["actions"],
        "source": source
    }