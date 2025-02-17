import json
import requests
from requests_aws4auth import AWS4Auth
import boto3

# OpenSearch Configuration
REGION = "us-east-1"
OPENSEARCH_HOST = "https://your-opensearch-endpoint.amazonaws.com"  # Replace with your OpenSearch domain
INDEX_NAME = "restaurants"

# AWS Authentication
session = boto3.Session()
credentials = session.get_credentials()

if credentials is None:
    raise ValueError(" Unable to retrieve AWS credentials. Please check IAM role permissions.")

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "es",
    session_token=credentials.token
)

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table("yelp-restaurants")  # Ensure the correct table name

def fetch_data_from_dynamodb():
    """
    Retrieve all restaurant data from DynamoDB.
    """
    print(" Fetching data from DynamoDB...")

    items = []
    last_evaluated_key = None

    while True:
        scan_params = {}
        if last_evaluated_key:
            scan_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.scan(**scan_params)
        items.extend(response.get("Items", []))

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break  # All data retrieved

    print(f" Retrieved {len(items)} items from DynamoDB.")
    return items


def insert_into_opensearch(data):
    """
    Insert data into OpenSearch in bulk.
    """
    url = f"{OPENSEARCH_HOST}/{INDEX_NAME}/_bulk"
    headers = {"Content-Type": "application/json"}

    bulk_data = ""
    for item in data:
        restaurant_id = item.get("BusinessID")
        cuisine = item.get("Cuisine")

        if not restaurant_id or not cuisine:
            continue  # Skip invalid data

        # OpenSearch bulk insert format
        bulk_data += json.dumps({"index": {"_index": INDEX_NAME, "_id": restaurant_id}}) + "\n"
        bulk_data += json.dumps({"RestaurantID": restaurant_id, "Cuisine": cuisine}) + "\n"

    if not bulk_data:
        print("No valid data available for OpenSearch insertion.")
        return {"statusCode": 400, "body": json.dumps("No valid data to insert")}

    response = requests.post(url, auth=awsauth, data=bulk_data, headers=headers)

    if response.status_code == 200:
        print(" Data successfully inserted into OpenSearch!")
        return {"statusCode": 200, "body": json.dumps(f"Inserted {len(data)} items into OpenSearch")}
    else:
        print(f" Insertion failed - Status Code: {response.status_code}")
        print(" Response:", response.text)
        return {"statusCode": response.status_code, "body": json.dumps(response.text)}


def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    """
    if event.get("action") == "insert_data":
        data = fetch_data_from_dynamodb()
        return insert_into_opensearch(data)

    return {"statusCode": 400, "body": json.dumps(" Invalid action. Please provide 'insert_data'.")}

