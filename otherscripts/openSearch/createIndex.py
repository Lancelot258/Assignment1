import json
import requests
from requests_aws4auth import AWS4Auth
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# OpenSearch Configuration
REGION = "your-region"
OPENSEARCH_HOST = "https://your-opensearch-domain.com"
INDEX_NAME = "restaurants"

# AWS Authentication
session = boto3.Session()
credentials = session.get_credentials()

if credentials is None:
    raise ValueError("AWS Credentials not found. Check IAM role permissions.")

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "es",
    session_token=credentials.token
)

def create_index():
    """
    Create the `restaurants` index in OpenSearch
    """
    url = f"{OPENSEARCH_HOST}/{INDEX_NAME}"
    headers = {"Content-Type": "application/json"}

    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1
        },
        "mappings": {
            "properties": {
                "RestaurantID": {"type": "keyword"},
                "Cuisine": {"type": "keyword"}
            }
        }
    }

    try:
        response = requests.put(url, auth=awsauth, json=index_settings, headers=headers)

        if response.status_code in [200, 201]:
            logger.info("Index created successfully!")
            return {"statusCode": 200, "body": json.dumps("Index created successfully")}
        else:
            logger.error(f"Failed to create index - Status Code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {"statusCode": response.status_code, "body": response.text}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"statusCode": 500, "body": json.dumps(f"Request failed: {e}")}

# Lambda entry point function
def lambda_handler(event, context):
    return create_index()

