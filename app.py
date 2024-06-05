from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Replace with your Make.com webhook endpoint
MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'

@app.route('/')
def home():
    return "Server is running."

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    try:
        if request.method == 'POST':
            user_input = request.form.get('message')
        elif request.method == 'GET':
            user_input = request.args.get('message')
        else:
            return jsonify({"error": "Unsupported HTTP method"})

        if not user_input:
            return jsonify({"error": "No message provided"})

        # Send HTTP POST request to Make.com with user input
        response = requests.post(MAKE_COM_ENDPOINT, json={'text': user_input})
        response_data = response.json()

        if response.status_code == 200:
            # Extract response data
            response_body = response_data.get('data', 'Error: No response from Make.com')
            # Log response
            app.logger.info(f"Response from Make.com: {response_body}")
            return jsonify({"user_input": user_input, "response_body": response_body})
        else:
            error_message = response_data.get('error', 'Failed to get a valid response from Make.com')
            app.logger.error(error_message)
            return jsonify({"error": error_message})

    except Exception as e:
        error_message = f'An error occurred: {str(e)}'
        app.logger.error(error_message)
        return jsonify({"error": error_message})

if __name__ == '__main__':
    app.run(debug=True)
