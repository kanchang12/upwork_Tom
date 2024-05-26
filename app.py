import os
from flask import Flask, render_template, request, jsonify
import requests
from fuzzywuzzy import process

app = Flask(__name__)

# Ensure your Make webhook URL is set in the environment variables
MAKE_WEBHOOK_URL = 'https://hook.eu2.make.com/v0vjdkn2f6msuakr7hxv86ztmk5ukttq'

# List of keywords for fuzzy matching
KEYWORDS = ["search", "query", "find", "lookup", "locate", "fetch", "is there", "attachment", "email"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_text", methods=["POST"])
def process_text():
    try:
        # Get the conversation from the request
        conversation = request.json.get('conversation')
        user_input = conversation[-1].get('content') if conversation else None

        # Perform fuzzy matching on the user input to detect keywords
        matched_keyword, score = process.extractOne(user_input, KEYWORDS)

        if score >= 50:  # Threshold for considering a match
            # If a keyword is found, send the user input directly to the next module
            payload = {
                "userInput": user_input
            }
            response = requests.post(MAKE_WEBHOOK_URL, json=payload)  # Send data as JSON

            # Check the response status and process accordingly
            if response.status_code == 200:
                make_response = response.json().get('answer')  # Get the 'answer' key from JSON response
                formatted_response = f'<div class="agent-message">{make_response}</div>'
                return jsonify({'answer': formatted_response})
            else:
                return jsonify({"error": "Failed to get response from Make"}), 400
        else:
            # If no keyword is found, handle the input differently (e.g., display a message)
            return jsonify({"error": "No relevant keyword found in input"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
