import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Ensure your Make webhook URL is set in the environment variables
MAKE_WEBHOOK_URL = 'https://hooks.zapier.com/hooks/catch/18968519/3vp1fzw/'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_text", methods=["POST"])
def process_text():
    try:
        conversation = request.json.get('conversation')
        user_input = conversation[-1].get('content') if conversation else None
        payload = {
            "userInput": user_input
        }

        response = requests.post(MAKE_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            make_response = response.text
            # Return HTML response
            return Response(make_response, mimetype='text/html')
        else:
            # Return error message as HTML
            error_message = "<h1>Failed to get response from Make</h1>"
            return Response(error_message, status=400, mimetype='text/html')

    except Exception as e:
        # Return error message as HTML
        error_message = "<h1>Error: {}</h1>".format(e)
        return Response(error_message, status=400, mimetype='text/html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
