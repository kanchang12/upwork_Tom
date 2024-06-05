from flask import Flask, render_template, request, jsonify, session
import requests
import sys
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key for session management

# Replace with your Make.com webhook endpoint
MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)

# Global variable to store callback data
processed_data = None

@app.route('/')
def home():
    global processed_data
    return render_template('index.html', response_data=processed_data)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global processed_data
    try:
        user_input = None
        if request.method == 'POST':
            if request.is_json:
                request_data = request.get_json()
                app.logger.info(f"Request JSON: {request_data}")
                user_input = request_data.get('message')
            else:
                user_input = request.form.get('message')
        elif request.method == 'GET':
            user_input = request.args.get('message')
        
        if not user_input:
            error_message = "Error: No message provided"
            app.logger.error(error_message)
            return jsonify({"user_input": None, "response_subject": None, "response_body": error_message}), 400

        # Send HTTP POST request to Make.com with user input
        response = requests.post(MAKE_COM_ENDPOINT, json={'text': user_input})
        app.logger.info(f"Response status code: {response.status_code}")
        app.logger.info(f"Response content: {response.content}")

        if response.status_code == 200 and response.text == 'Accepted':
            # Successfully sent request to Make.com
            processed_data = None  # Reset processed data
            return jsonify({"user_input": user_input, "response_subject": "Request Accepted", "response_body": "Processing, please wait for the result."})
        else:
            error_message = 'Error: Failed to get a valid response from Make.com'
            app.logger.error(error_message)
            return jsonify({"user_input": user_input, "response_subject": None, "response_body": error_message}), 500

    except Exception as e:
        error_message = f'An error occurred: {str(e)}'
        app.logger.error(error_message)
        return jsonify({"user_input": user_input, "response_subject": None, "response_body": error_message}), 500

@app.route('/callback', methods=['POST'])
def callback():
    global processed_data
    try:
        callback_data = request.get_json()
        app.logger.info(f"Callback data received: {callback_data}")

        # Store the processed data in session
        session['processed_data'] = callback_data

        return jsonify({"status": "success", "data": callback_data}), 200

    except Exception as e:
        error_message = f'An error occurred in callback: {str(e)}'
        app.logger.error(error_message)
        return jsonify({"status": "error", "message": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
