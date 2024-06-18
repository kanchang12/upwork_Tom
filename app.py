from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import openai
from bson import json_util
import copy

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
MONGODB_URI = "mongodb+srv://kanchang12:Ob3uROyf8rtbEOwx@cluster0.sle630c.mongodb.net/upwrok?retryWrites=true&w=majority"
MONGODB_DB_NAME = "upwrok"
MONGODB_COLLECTION_NAME = "files"

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]
properties_collection = db[MONGODB_COLLECTION_NAME]
conversations_collection = db["conversations"]

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Step 1: Read the database and get all consolidated data and conversations in variables
consolidated_data = list(properties_collection.find())
conversations = list(conversations_collection.find())

# Function to interact with OpenAI GPT-3.5 model
def get_gpt_response(user_input, context, conversation_history):
    system_prompt = f"""
    You are Nia, a conversational AI assistant that can provide concise and natural responses to queries based on the provided context. You should be able to identify, count, and summarize relevant information from the context in a conversational manner, avoiding overly detailed or robotic responses.

    for example if user asks how many cleaners are there, you should check all the properties and count where cleaners info are given

    This will be done for all cases like properties, employees and anything

    Your answers has to be one line to the point, you need to remember continuing conversation to answer. So if the user asks how many properties and then next question which one: you need to understand based on both the comments and not the last one only

    Conversation History: {conversation_history}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context: {context}\n\nQuery: {user_input}"}
    ]

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        temperature=0.7,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    generated_text = response.choices[0].message.content
    return generated_text

def update_consolidated_data():
    global consolidated_data
    consolidated_data = list(properties_collection.find())
    # Commit the changes to the database
    client.commit()

def append_new_conversation(conversation_history):
    conversations_collection.insert_one({"conversation": conversation_history})

def update_record(property_name, field_name, new_value):
    record = properties_collection.find_one({"property_name": {"$regex": f"^{property_name}$", "$options": "i"}})
    if record:
        previous_value = copy.deepcopy(record.get(field_name))
        result = properties_collection.update_one(
            {"property_name": {"$regex": f"^{property_name}$", "$options": "i"}},
            {"$set": {field_name: new_value}}
        )
        if result.modified_count > 0:
            response_text = f"Updated {field_name} of {property_name} from {previous_value} to {new_value}"
            update_consolidated_data()  # Call the function to update consolidated_data
            # Commit the changes to the database
            client.commit()
        else:
            response_text = f"Failed to update {field_name} of {property_name}"
    else:
        response_text = f"No property found with the name '{property_name}'"
    return response_text

# Function to process user's query
def process_query(query):
    conversation_history = ""
    for conversation in conversations:
        conversation_history += conversation.get("conversation", "") + "\n"

    # Step 2: Take user input and put it in an AI engine to find out what the user is asking
    intent_response = get_gpt_response(query, json_util.dumps(consolidated_data), conversation_history)
    conversation_history += f"User: {query}\nAI: {intent_response}\n"

    # Step 3: Depending on user needs, return a query (it can be general like Hi, hello, what is New York, or very specific to the data)
    query_response = get_gpt_response(intent_response, json_util.dumps(consolidated_data), conversation_history)
    conversation_history += f"User: {intent_response}\nAI: {query_response}\n"

    # Step 4: The query will be given to another LLM which will use the variable data to return the correct value
    result_response = get_gpt_response(query_response, json_util.dumps(consolidated_data), conversation_history)
    conversation_history += f"User: {query_response}\nAI: {result_response}\n"

    # Check if the user's intent is to update a record
    if "update record" in result_response.lower():
        try:
            property_name, field_name, new_value = result_response.lower().split("update record")[1].strip().split(",")
            property_name = property_name.strip()
            field_name = field_name.strip()
            new_value = new_value.strip()
            response_text = update_record(property_name, field_name, new_value)
        except ValueError:
            response_text = "Please provide the property name, field name, and new value in the correct format."
    else:
        response_text = result_response

    append_new_conversation(conversation_history)

    return response_text

# Route to handle user queries
@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query')
    response_text = process_query(query)
    return jsonify({'response': response_text})

# Serve the HTML file
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
