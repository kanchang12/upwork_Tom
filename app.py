from flask import Flask, render_template, request, jsonify
import requests
import sys
import logging

app = Flask(__name__)

# Replace with your Make.com webhook endpoint
MAKE_COM_ENDPOINT = 'https://hook.eu2.make.com/kv24kv7cddrvnuundv60a7mdk99lmxsu'

# Configure logging to print to console
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    try:
        if request.method == 'POST':
            user_input = request.form['message']
        elif request.method == 'GET':
            user_input = request.args.get('message')
        
        # Send HTTP POST request to Make.com with user input
        response = requests.post(MAKE_COM_ENDPOINT, json={'text': user_input})
        response.raise_for_status()  # Raise an exception for 4XX or 5XX status codes

        make_response = response.json().get('data', 'Error: No response from Make.com')

        # Log the user input and response
        app.logger.info(f"User Input: {user_input}")
        app.logger.info(f"Make.com Response: {make_response}")

        return jsonify({"user_input": user_input, "response": make_response})

    except requests.exceptions.RequestException as e:
        error_message = f'Error: {str(e)}'
        app.logger.error(error_message)
        return jsonify({"user_input": user_input, "response": error_message})

    except Exception as e:
        error_message = f'An error occurred: {str(e)}'
        app.logger.error(error_message)
        return jsonify({"user_input": user_input, "response": error_message})

if __name__ == '__main__':
    app.run(debug=True)
