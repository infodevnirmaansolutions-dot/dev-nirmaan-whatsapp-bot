import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Environment Variables
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "DevNirmaanSecret123")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini AI Setup
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """
आप Dev Nirmaan Solutions के आधिकारिक AI असिस्टेंट हैं।
आपका नाम Dev Nirmaan Bot है।
कंपनी सिविल इंजीनियरिंग, कंस्ट्रक्शन, बिल्डिंग डिज़ाइन, साइट एग्ज़ीक्यूशन, एपॉक्सी फ़्लोरिंग और आर्किटेक्चरल सर्विसेज प्रदान करती है।
आप ग्राहकों के सवालों का जवाब नम्रता, पेशेवर और सटीक हिंदी/अंग्रेज़ी में देंगे।
"""

@app.route("/", methods=["GET"])
def home():
    return "Dev Nirmaan WhatsApp Bot is Running!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403
    return "Bad Request", 400

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])

                    if messages:
                        message = messages[0]
                        from_number = message.get("from")
                        text_body = message.get("text", {}).get("body", "")

                        if text_body:
                            prompt = f"{SYSTEM_PROMPT}\n\nग्राहक का सवाल: {text_body}"
                            response = model.generate_content(prompt)
                            ai_reply = response.text
                            send_whatsapp_message(from_number, ai_reply)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"status": "error"}), 500

def send_whatsapp_message(to_phone, message_text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message_text}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
