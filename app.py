from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import time
import sys
import logging

app = Flask(__name__)

# Replace with your Make.com webhook endpoint
MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
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
        time.sleep(10)  # Consider asynchronous methods for better performance

        app.logger.info(f"Response status code: {response.status_code}")
        app.logger.info(f"Response content: {response.content}")

        if response.status_code == 200:
            try:
                make_response = response.json().get('data', 'Error: No response from Make.com')

                # Parse HTML response to extract message details
                soup = BeautifulSoup(make_response, 'html.parser')
                # Extract message subject
                subject = soup.find('h2').text if soup.find('h2') else "No subject found"
                # Extract message body
                body = soup.find('p').text if soup.find('p') else "No body found"

                # Log extracted subject and body
                app.logger.info(f"Subject: {subject}")
                app.logger.info(f"Body: {body}")

                return jsonify({"user_input": user_input, "response_subject": subject, "response_body": body})
            except ValueError as e:
                error_message = f"Error parsing response JSON: {str(e)}"
                app.logger.error(error_message)
                return jsonify({"user_input": user_input, "response_subject": None, "response_body": error_message}), 500
        else:
            error_message = 'Error: Failed to get a valid response from Make.com'
            app.logger.error(error_message)
            return jsonify({"user_input": user_input, "response_subject": None, "response_body": error_message}), 500

    except Exception as e:
        error_message = f'An error occurred: {str(e)}'
        app.logger.error(error_message)
        return jsonify({"user_input": user_input, "response_subject": None, "response_body": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
