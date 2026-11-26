import os

from flask import Flask, render_template, request, jsonify
from backend.chatbot import chatbot_response
from backend.knowledge_base import SCENARIOS
from backend.fraud_detector import detect_fraud

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    if len(message) > 3000:
        return jsonify({"error": "Message is too long."}), 400

    # Each browser sends its own random id, so two people on the same
    # Wi-Fi / IP address never share a chat history.
    session_id = str(data.get("session_id", "default"))[:64]

    result = chatbot_response(message, session_id)

    return jsonify(result)


@app.route("/api/scenarios")
def scenarios():
    return jsonify(SCENARIOS)


@app.route("/api/check", methods=["POST"])
def check():

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Enter a message to check."}), 400

    return jsonify(detect_fraud(message))


if __name__ == "__main__":
    # debug=True is only for your own computer. Set FLASK_DEBUG=0 when you deploy.
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1") 