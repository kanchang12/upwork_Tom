import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Ensure your Make webhook URL is set in the environment variables
MAKE_WEBHOOK_URL = 'https://hooks.zapier.com/hooks/catch/18968519/3vp1fzw/'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send_to_make", methods=["POST"])
def send_to_make():
    try:
        user_input = request.json.get('userInput')
        payload = {
            "userInput": user_input
        }
    
        response = requests.post(MAKE_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            make_response = response.json().get('data')
            return jsonify({'answer': make_response})
        else:
            return jsonify({"error": "Failed to get response from Make"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
