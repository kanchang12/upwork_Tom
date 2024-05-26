from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return "Webhook Receiver"

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        # Print the received JSON data to the console
        print("Received JSON data:", data)
        
        # Send a response back
        return jsonify({'status': 'success', 'received_data': data})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
