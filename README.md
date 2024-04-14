# AIamond GPT Backend

This is a Serverless application that uses AWS Lambda and the OpenAI GPT model.
The main purpose is to provide a FLASK API BACKEND to be used in a private app / webui to talk to OpenAIs GPT4Turbo model.

## Prerequisites

You will need an OpenAI Account with payments to use the GPT4. You could use the free version, but you have to change the environment vars to both use GPT3.

- Node.js and npm
- Python 3.11
- Serverless Framework
- AWS CLI
- Git

## Installation

Three environment vars are needed:

```bash
OPENAI_API_KEY=.....
GPT3_MODEL=gpt-3.5-turbo
GPT4_MODEL=gpt-4-turbo
```

```bash
git clone https://github.com/Kipperlenny/aiamond_gptbackend.git
cd aiamond_gptbackend
npm install -g serverless
pip install -r requirements.txt
npx dotenv -e .env -- serverless deploy
```

## Usage

After deploying, you can call your API Gateway endpoint with a POST request to interact with the GPT model. You need to authenticate with the AWS IAM User created during serverless deployment (get the access data from aws console!).

This Flask application provides the following endpoints:

# Start Conversation

Endpoint: /start_conversation
Method: POST
Data Params: title (optional)
Success Response: {"conversation_id": "<conversation_id>"} with HTTP status 201
Description: Starts a new conversation and returns its ID.

# Add to Conversation

Endpoint: /add_to_conversation
Method: POST
Data Params: conversation_id (optional), question
Success Response: {"response": "<response>", "conversation_id": "<conversation_id>"} with HTTP status 200
Description: Adds a question to a conversation and returns the assistant's response.

# List Conversations

Endpoint: /list_conversations
Method: GET
Success Response: A list of conversations with their IDs and titles, with HTTP status 200
Description: Returns a list of all conversations.

# Get Conversation

Endpoint: /get_conversation/<conv_id>
Method: GET
URL Params: conv_id
Success Response: The conversation history, with HTTP status 200
Error Response: {"error": "Conversation not found"} with HTTP status 404
Description: Returns the history of a conversation.

# Delete Conversation

Endpoint: /delete_conversation/<conv_id>
Method: DELETE
URL Params: conv_id
Success Response: {"message": "Conversation deleted"} with HTTP status 200
Error Response: {"error": "Conversation not found"} with HTTP status 404
Description: Deletes a conversation.

Please note that all data sent and received is in JSON format.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[GPL 3.0](https://choosealicense.com/licenses/gpl-3.0/)

