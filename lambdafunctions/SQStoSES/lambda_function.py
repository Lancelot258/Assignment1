import json
import boto3
import requests
from requests_aws4auth import AWS4Auth
import random
import os

# AWS Configurations
REGION = "your-region"
SQS_URL = "https://sqs.your-region.amazonaws.com/your-account-id/YourQueueName"
OPENSEARCH_HOST = "https://your-opensearch-domain.com"
INDEX_NAME = "restaurants"
DYNAMODB_TABLE = "your-dynamodb-table"
SES_SENDER_EMAIL = "your-email@example.com"

# AWS Clients
session = boto3.Session()
credentials = session.get_credentials()

if credentials is None:
    raise ValueError(" AWS Credentials not found. Check IAM permissions.")

awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, "es", session_token=credentials.token)
sqs = boto3.client("sqs", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
ses = boto3.client("ses", region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

def get_sqs_message():
    """Fetch a message from SQS Queue (Q1)."""
    response = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=2)
    messages = response.get("Messages", [])
    if not messages:
        print("No messages in SQS queue.")
        return None
    return messages[0]

def delete_sqs_message(receipt_handle):
    """Delete processed message from SQS queue."""
    sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)

def get_restaurant_recommendation(cuisine):
    """Fetch a random restaurant from OpenSearch based on cuisine."""
    url = f"{OPENSEARCH_HOST}/{INDEX_NAME}/_search"
    headers = {"Content-Type": "application/json"}
    query = {
        "size": 5,
        "query": {
            "match": {
                "Cuisine": cuisine
            }
        }
    }
    response = requests.get(url, auth=awsauth, json=query, headers=headers)
    if response.status_code != 200:
        print(f" OpenSearch error: {response.text}")
        return None

    hits = response.json().get("hits", {}).get("hits", [])
    if not hits:
        print(f"No restaurants found for cuisine: {cuisine}")
        return None
    
    return random.choice(hits)["_source"]

def get_restaurant_details(restaurant_id):
    """Fetch restaurant details from DynamoDB."""
    response = table.get_item(Key={"BusinessID": restaurant_id})
    return response.get("Item", {})

def send_email(to_email, subject, body):
    """Send recommendation email using AWS SES."""
    response = ses.send_email(
        Source=SES_SENDER_EMAIL,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": body}}
        }
    )
    return response

def lambda_handler(event, context):
    """Main Lambda handler for processing queue and sending recommendations."""
    
    message = get_sqs_message()
    if not message:
        return {"statusCode": 200, "body": json.dumps("No messages to process")}

    receipt_handle = message["ReceiptHandle"]
    body = json.loads(message["Body"])
    cuisine = body.get("cuisine")
    email = body.get("email")

    if not cuisine or not email:
        print(" Missing data in SQS message. Deleting it.")
        delete_sqs_message(receipt_handle)
        return {"statusCode": 400, "body": json.dumps("Invalid SQS message")}

    print(f" Processing request for: {email}, Cuisine: {cuisine}")

    restaurant = get_restaurant_recommendation(cuisine)
    if not restaurant:
        delete_sqs_message(receipt_handle)
        return {"statusCode": 404, "body": json.dumps("No restaurant found")}

    restaurant_details = get_restaurant_details(restaurant["RestaurantID"])
    restaurant_name = restaurant_details.get("Name", "Unknown Restaurant")
    address = restaurant_details.get("Address", "Unknown Address")

    subject = f" Your {cuisine} restaurant recommendation"
    email_body = f"""
    Hi,

    Based on your request, we recommend:

    Restaurant: {restaurant_name}
    Cuisine: {cuisine}
    Address: {address}

    Enjoy your meal! 
    """

    send_email(email, subject, email_body)
    print(f" Email sent to {email}")

    delete_sqs_message(receipt_handle)

    return {"statusCode": 200, "body": json.dumps("Email sent successfully")}


