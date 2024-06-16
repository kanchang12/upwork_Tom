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
MONGODB_URI = "mongodb+srv://kanchang12:Ob3uROyf8rtbEOwx@cluster0.sle630c.mongodb.net/upwrok?retryWrites=true&w=majority&ssl=true"
MONGODB_DB_NAME = "upwrok"
MONGODB_COLLECTION_NAME = "files"

# Initialize MongoDB client with SSL parameters
client1 = MongoClient(MONGODB_URI)
db = client1.get_database(MONGODB_DB_NAME)
collection = db.get_collection(MONGODB_COLLECTION_NAME)

def read_files_from_database(collection):
    aggregated_text = ""
    cursor = collection.find({}, {"content": 1, "_id": 0})
    for doc in cursor:
        file_content = doc.get("content", "")
        aggregated_text += str(file_content) + "\n"
    return aggregated_text.strip()

def update_aggregate_text():
    aggregated_text = read_files_from_database(collection)
    return aggregated_text

def search_database(query):
    """Search the MongoDB database for the query and return relevant results."""
    search_results = []
    cursor = collection.find({"content": {"$regex": re.escape(query), "$options": "i"}})
    for doc in cursor:
        search_results.append(doc.get("content", ""))
    return search_result

@app.route('/')
def index():
    return render_template('index.html')

openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

conversation_history = "Your initial system instructions here..."

def get_response(user_input, conversation_history):
    try:
        # Search the database for the user query
        search_results = search_database(user_input)
        
        # Format the search results
        search_response = "\n".join(search_results)
        
        # Generate response using OpenAI GPT
        messages = [
            {"role": "system", "content": conversation_history},
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

def get_claude_response(user_input):
    global conversation_history
    aggregated_text = update_aggregate_text()

    system_instructions = f"""
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
    Chatbot: "The Brick property is X miles from the nearest airport.""

    """

    # Update conversation history with new instructions
    conversation_history = f"{conversation_history}\n{system_instructions}"

    # Truncate conversation history to fit within the model's token limit
    max_token_limit = 16385 - 2560  # Model's max tokens - response max tokens
    truncated_history = truncate_conversation_history(conversation_history, max_token_limit)

    generated_text, conversation_history = get_response(user_input, truncated_history)
    
    return generated_text, conversation_history

def truncate_conversation_history(history, max_tokens):
    """Truncate conversation history to fit within the token limit."""
    tokens = history.split()
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[-max_tokens:]
        return ' '.join(truncated_tokens)
    return history

@app.route('/process_command', methods=['POST'])
def process_command():
    global conversation_history
    user_input = request.json.get("user_input")
    if not user_input:
        return jsonify({"response": "No user input provided."}), 400

    response_text, conversation_history = get_response(user_input, conversation_history)
    return jsonify({"response": response_text})

def update_record(db, file_name, variable_name, new_value):
    collection = db[MONGODB_COLLECTION_NAME]
    doc = collection.find_one({"filename": file_name})
    if not doc:
        return f"File {file_name} not found in the database"

    content = doc.get("content", "")
    lines = str(content).split("\n")
    updated_lines = []
    matched_variable = None
    for line in lines:
        if variable_name.lower() in line.lower():
            matched_variable = line.split(":")[0].strip()
            old_value = line.split(":")[1].strip()
            new_line = f"{matched_variable}: {new_value}\nPrevious Value: {old_value}"
            updated_lines.append(new_line)
        else:
            updated_lines.append(line)

    if matched_variable is None:
        return f"Variable {variable_name} not found in file {file_name}"

    new_content = "\n".join(updated_lines)
    collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"content": new_content}}
    )
  
    update_aggregate_text()

    return f"Updated {file_name}: {variable_name} set to {new_value}, Previous {variable_name} = \"{old_value}\""

if __name__ == '__main__':
    app.run(debug=True)
