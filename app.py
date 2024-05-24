import os
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# Set up OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Preset instruction for the agent
preset_instruction = "Consider yourself as a Finance advisor. Talk like one. Please limit all your responses in short 2 lines. Unless the user specifically requests to explain."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_text", methods=["POST"])
def process_text():
    if request.method == "POST":
        try:
            conversation = request.json.get('conversation', [])

            # Construct the initial system message based on the preset instruction
            if not any(msg['role'] == 'system' for msg in conversation):
                conversation.insert(0, {"role": "system", "content": preset_instruction})

            # Send the messages to OpenAI for chat completion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=conversation,
                max_tokens=150
            )

            # Get the response text from the model's response
            response_text = response['choices'][0]['message']['content']

            return jsonify({'answer': response_text})

        except Exception as e:
            return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    # Use Gunicorn as the production WSGI server
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
