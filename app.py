import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Dev Nirmaan Solutions WhatsApp Bot is Live!", 200

# Initialize the Gemini client (it automatically picks up GEMINI_API_KEY from environment variables)
client = genai.Client()

SYSTEM_PROMPT = """आप 'Dev Nirmaan Solutions' के एक विशेषज्ञ सिविल इंजीनियरिंग और कंस्ट्रक्शन कंसलटेंट हैं। 
रमेश चंद्र इस संस्था के फाउंडर हैं। आप ग्राहकों को घर बनाने, नक्शे, लागत, सामग्री (जैसे सीमेंट, सरिया, एपॉक्सी फ़्लोरिंग, आरसीसी) और साइट एक्जीक्यूशन से जुड़ी सटीक और पेशेवर सलाह देते हैं। हमेशा हिंदी या आसान हिंग्लिश में पेशेवर और मददगार जवाब दें।"""

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "DevNirmaanSecret123")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Hello World", 200

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
                        sender_phone = message.get("from")
                        message_body = message.get("text", {}).get("body", "")

                        if message_body:
                            # Generate response using the correct Gemini model name
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=f"{SYSTEM_PROMPT}\n\nग्राहक का संदेश: {message_body}"
                            )
                            reply_text = response.text

                            # Send reply back via WhatsApp Cloud API
                            headers = {
                                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "messaging_product": "whatsapp",
                                "to": sender_phone,
                                "type": "text",
                                "text": {"body": reply_text}
                            }
                            requests.post(
                                f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages",
                                json=payload,
                                headers=headers
                            )
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
