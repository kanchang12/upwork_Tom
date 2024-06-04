from flask import Flask, render_template, request, jsonify
import requests
import time

app = Flask(__name__)

# Replace with your Make.com webhook endpoint
MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'

@app.route('/')
def home():
    # Pass any necessary context variables (e.g., 'response') to the template
    return render_template('index.html', response="Hello from Flask!")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.form['message']

        # Send HTTP POST request to Make.com with user input
        response = requests.post(MAKE_COM_ENDPOINT, json={'text': user_input})
        time.sleep(10)  # Consider asynchronous methods for better performance

        if response.status_code == 200:
            make_response = response.json().get('response', 'Error: No response from Make.com')
            return jsonify({"user_input": user_input, "response": make_response})
        else:
            return jsonify({"user_input": user_input, "response": f"Error: Failed to send message to Make.com (HTTP {response.status_code})"})

    except Exception as e:
        error_message = 'An error occurred. Please try again later.'
        return jsonify({"user_input": user_input, "response": error_message})

if __name__ == '__main__':
    app.run(debug=True)
