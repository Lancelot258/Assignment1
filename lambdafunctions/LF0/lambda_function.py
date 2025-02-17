import json
import boto3

# Initialize Lex runtime client
client = boto3.client('lexv2-runtime', region_name='your_region_name')

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event, indent=2))  # Debug Log

        # Check if event contains body
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS, POST, GET',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'message': 'Invalid request. Missing body.'})
            }

        # Parse JSON data from frontend
        body = json.loads(event["body"])  # Ensure JSON parsing
        user_message = body.get("message", "")

        # Call Lex bot
        lex_response = client.recognize_text(
            botId='YOUR_BOT_ID',         # Lex bot ID
            botAliasId='YOUR_BOT_ALIAS_ID',    # Lex bot alias ID (ensure correct value)
            localeId='en_US',           # Language
            sessionId='YOUR_SESSION_ID',   # Can be replaced with user ID
            text=user_message
        )

        # Retrieve Lex response
        messages = lex_response.get('messages', [])
        bot_response = messages[0]['content'] if messages else "Sorry, I didn't understand that."

        # Return API response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': bot_response})
        }

    except Exception as e:
        print(f"Error: {str(e)}")  # Debug Log
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Error processing request'})
        }

