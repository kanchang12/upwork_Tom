from flask import Flask, request, jsonify, render_template
import requests
import os
import time

app = Flask(__name__)

# Reading the secret key from environment variables
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')

# Replace this with your Make.com webhook endpoint
MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'

def process_response(response):
    try:
        # Try to parse the response as JSON
        json_response = response.json()
        return json_response
    except ValueError:
        # If parsing as JSON fails, assume it's HTML
        return {'html_response': response.text}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message')

        if not message:
            return jsonify({'error': 'No message provided'})

        # Send request to Make.com
        response = requests.post(MAKE_COM_ENDPOINT, json={'message': message})

        if response.status_code == 200:
            # Process the response
            processed_response = process_response(response)
            return jsonify(processed_response)
        else:
            return jsonify({'error': f'Request failed with status code {response.status_code}'})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
