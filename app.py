import requests
from flask import Flask, request, jsonify, render_template
import pymongo
import openai
import re
import os
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB connection details
MONGODB_URI = "mongodb+srv://kanchang12:Ob3uROyf8rtbEOwx@cluster0.sle630c.mongodb.net/upwrok?retryWrites=true&w=majority&ssl=true"
MONGODB_DB_NAME = "upwrok"
MONGODB_COLLECTION_NAME = "files"

# Initialize MongoDB client
client1 = MongoClient(MONGODB_URI)
db = client1.get_database(MONGODB_DB_NAME)
collection = db.get_collection(MONGODB_COLLECTION_NAME)

@app.route('/')
def index():
    return render_template('index.html')

# OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

conversation_history = """
Purpose:
    Your primary goal is to provide accurate, concise responses to assist the business owner. You will use the data in the variable {aggregated_text} and, if needed, refer to your public training data.

    General Rules:
    Understand User Intent: Classify each question into one of four categories:

    ADD RECORD
    UPDATE RECORD
    SET ALERT
    FETCH RECORD
    Response Style:

    Provide to-the-point answers.
    Responses should be a maximum of 15 words.
    Use spaces between words, not new line characters.
    Direct Responses: Do not ask unnecessary questions. If the user asks for specific information, provide it directly.

    FETCH RECORD:
    Property Names: If asked for property names, list all properties without asking for confirmation.
    Property Count: If asked for the number of properties, state the number and ask if names are needed.
    Specific Information: If asked for details like cleaner or contractor names, provide the specific name.
    Distance to Airport: Calculate the distance from the property address to the nearest airport and provide the answer.
    UPDATE RECORD:
    Format: Use the format UPDATE RECORD [Location] *[Variable Name]* [New Value]
    Variable Names: Ensure variable names are enclosed in asterisks (*).
    Variable Names:
    Location
    Type
    Address
    Room setup
    Employee name
    Employee role
    Cell phone
    Talk route
    Facebook link
    Garbage day
    Platforms advertised
    Cleaners info
    Property checker
    Pool cleaner
    Lawn Maintenance
    Furniture cleaner
    Hvac contractor
    Plumbing contractor
    Electrical contractor
    Appliance contractor
    Insurance
    Electric bill
    Water bill
    Gas bill
    Internet bill
    Mortgage
    Contextual Understanding:
    Clarifications: If the property name is unclear or mispronounced, clarify if not understandable. Otherwise, proceed with the best match.
    Implicit Information: If the user implies information (e.g., asking for an employee name without mentioning the property but then providing it), do not ask again for confirmation.
    Examples:
    Example 1: Property Names Request

    User: "What are the properties we have at New Jersey?"

    Response: "Properties in New Jersey: [List all property names]."

    Incorrect Approach:

    User: "What are the properties we have at New Jersey?"
    Chatbot: "We have properties in New Jersey. Would you like to know the names of the properties?"
    User: "Yes, that is what I asked. What are the properties?"
    Chatbot: "There are multiple properties. Do you want the names of all properties?"
    Correct Approach:

    User: "What are the properties we have at New Jersey?"
    Chatbot: "Properties in New Jersey: [List all property names]."
    Example 2: Number of Properties

    User: "How many properties do we have in New Jersey?"

    Response: "We have X properties. Do you want their names?"

    Incorrect Approach:

    User: "How many properties do we have in New Jersey?"
    Chatbot: "We have properties in New Jersey. Would you like to know the names of the properties?"
    User: "Yes, I do."
    Chatbot: "There are multiple properties. Do you want the names of all properties?"
    Correct Approach:

    User: "How many properties do we have in New Jersey?"
    Chatbot: "We have X properties. Do you want their names?"
    Example 3: Updating Records

    User: "Change the employee in Brick property to Tom."

    Response: "UPDATE RECORD Brick Employee Name Tom"

    Incorrect Approach:

    User: "Change the employee in Brick property to Tom."
    Chatbot: "Do you mean the employee name?"
    User: "Yes, change the employee name to Tom."
    Chatbot: "Do you want to update the employee name for Brick property?"
    Correct Approach:

    User: "Change the employee in Brick property to Tom."
    Chatbot: "UPDATE RECORD Brick Employee Name Tom"
    Example 4: Cleaner Information

    User: "Who is the cleaner for the Brick property?"

    Response: "[Cleaner’s Name]"

    Incorrect Approach:

    User: "Who is the cleaner for the Brick property?"
    Chatbot: "Do you want the cleaner's name for Brick property?"
    User: "Yes."
    Chatbot: "The cleaner for Brick property is [Cleaner’s Name]."
    Correct Approach:

    User: "Who is the cleaner for the Brick property?"
    Chatbot: "[Cleaner’s Name]"
    Example 5: Distance to Airport

    User: "How far is the Brick property from the airport?"

    Response: "The Brick property is X miles from the nearest airport."

    Incorrect Approach:

    User: "How far is the Brick property from the airport?"
    Chatbot: "Do you want to know the distance from Brick property to the airport?"
    User: "Yes."
    Chatbot: "The Brick property is X miles from the nearest airport."
    Correct Approach:

    User: "How far is the Brick property from the airport?"
    Chatbot: "The Brick property is X miles from the nearest airport."
"""

def read_files_from_database(collection):
    """Reads all the text from the files stored in the database and aggregates it."""
    aggregated_text = ""
    for document in collection.find():
        aggregated_text += document.get("content", "") + "\n"
    return aggregated_text

def search_database(query):
    """Search the MongoDB database for the query and return relevant results."""
    search_results = []
    cursor = collection.find({"content": {"$regex": re.escape(query), "$options": "i"}})
    for doc in cursor:
        search_results.append(doc.get("content", ""))
    return search_results

def get_response(user_input, conversation_history):
    try:
        aggregated_text = read_files_from_database(collection)

        # Search the database for the user query
        search_results = search_database(user_input)

        # If no search results are found, handle it gracefully
        if not search_results:
            search_response = "No relevant information found in the database."
        else:
            # Format the search results
            search_response = "\n".join(search_results)

        # Truncate conversation history to stay within token limit
        max_tokens = 16385 - 2560  # maximum allowed tokens minus response tokens
        truncated_history = truncate_conversation_history(conversation_history, max_tokens)

        # Generate response using OpenAI GPT
        messages = [
            {"role": "system", "content": truncated_history.format(aggregated_text=aggregated_text)},
            {"role": "user", "content": user_input},
            {"role": "system", "content": f"Search results: {search_response}"}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=1,
            max_tokens=2560,
            top_p=1,
            frequency_penalty=0.9
        )

        generated_text = response.choices[0].message['content']

        # Update conversation history
        conversation_history += f"\nUser: {user_input}\nAssistant: {generated_text}"

        return generated_text, conversation_history
    except Exception as e:
        return f"Error in get_response: {str(e)}", conversation_history

def truncate_conversation_history(conversation_history, max_tokens):
    tokens = conversation_history.split()
    if len(tokens) > max_tokens:
        tokens = tokens[-max_tokens:]
    return ' '.join(tokens)

@app.route('/process_command', methods=['GET', 'POST'])
def process_command():
    global conversation_history
    if request.content_type == 'application/json':
        user_input = request.json.get("user_input")
    elif request.content_type == 'application/x-www-form-urlencoded':
        user_input = request.form.get("user_input")
    else:
        return jsonify({"error": "Unsupported Media Type. Content-Type must be application/json or application/x-www-form-urlencoded"}), 415

    if not user_input:
        return jsonify({"response": "No user input provided."}), 400

    # Check if the user input is an update command
    if user_input.startswith("UPDATE RECORD"):
        words = user_input.split()
        if len(words) >= 4:
            file_name = words[2]
            variable_name = words[3].strip('*')
            new_value = ' '.join(words[4:])
            result = collection.update_one(
                {"filename": file_name},
                {"$set": {variable_name: new_value}}
            )
            if result.modified_count > 0:
                return jsonify({"response": f"Record updated successfully: {file_name} {variable_name} = {new_value}"})
            else:
                return jsonify({"response": "No matching record found to update."})
        else:
            return jsonify({"response": "Invalid update command format."})

    response_text, conversation_history = get_response(user_input, conversation_history)
    return jsonify({"response": response_text})

@app.route('/aggregate_data', methods=['GET'])
def aggregate_data():
    try:
        aggregated_text = read_files_from_database(collection)
        return jsonify({"message": "Data aggregated successfully.", "aggregated_text": aggregated_text})
    except Exception as e:
        return jsonify({"message": f"Error during aggregation: {str(e)}"}), 500

@app.route('/regenerate_token_background', methods=['POST'])
def regenerate_token_background():
    try:
        # Logic to regenerate the token
        return jsonify({"message": "Token regenerated successfully."})
    except Exception as e:
        return jsonify({"message": f"Error regenerating token: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
