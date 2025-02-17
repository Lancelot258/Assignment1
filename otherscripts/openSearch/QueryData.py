import json
import requests
from requests_aws4auth import AWS4Auth
import boto3

# OpenSearch Configuration
REGION = "us-east-1"
OPENSEARCH_HOST = "https://your-opensearch-endpoint.amazonaws.com"  # Replace with your OpenSearch domain
INDEX_NAME = "restaurants"

# Get AWS Credentials
session = boto3.Session()
credentials = session.get_credentials()

if credentials is None:
    raise ValueError("❌ Unable to retrieve AWS credentials. Please check IAM role permissions.")

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "es",
    session_token=credentials.token
)

def fetch_all_data():
    """
    Retrieve all data from the OpenSearch `restaurants` index.
    """
    url = f"{OPENSEARCH_HOST}/{INDEX_NAME}/_search"
    headers = {"Content-Type": "application/json"}

    query = {
        "query": {
            "match_all": {}  # Retrieve all data
        }
    }

    response = requests.get(url, auth=awsauth, json=query, headers=headers)

    if response.status_code == 200:
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        print(f"✅ OpenSearch returned {len(hits)} records:")
        for hit in hits:
            print(hit["_source"])  # Print only the data portion
        return {"statusCode": 200, "body": json.dumps(hits)}
    else:
        print(f"❌ Query failed - Status Code: {response.status_code} - Response: {response.text}")
        return {"statusCode": response.status_code, "body": response.text}

def lambda_handler(event, context):
    """
    AWS Lambda entry point to query OpenSearch data.
    """
    return fetch_all_data()

