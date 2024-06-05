from flask import Flask, request, jsonify, render_template
import requests
import time

app = Flask(__name__)

MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'  # Replace with the actual endpoint

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
                user_input = request_data.get('message')
            else:
                user_input = request.form.get('message')

        if not user_input:
            error_message = "Error: No message provided"
            app.logger.error(error_message)
            return jsonify({"user_input": None, "response_subject": None, "response_body": error_message}), 400

        # Send HTTP POST request to Make.com with user input
        response = requests.post(MAKE_COM_ENDPOINT, json={'text': user_input})
        time.sleep(10)  # Wait for 10 seconds

        app.logger.info(f"Response status code: {response.status_code}")
        app.logger.info(f"Response content: {response.content}")

        if response.status_code == 200:
            try:
                make_response = response.choices[0].message['content']
                return render_template('index.html', user_input=user_input, make_response=make_response)
            except ValueError as e:
                app.logger.error(f"Error parsing response JSON: {str(e)}")
                return jsonify({"error": str(e)}), 500
        else:
            app.logger.error(f"Failed to get a valid response from Make.com. Status code: {response.status_code}")
            return jsonify({"error": "Failed to get a valid response from Make.com"}), 500

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
