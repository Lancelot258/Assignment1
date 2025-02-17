import json
import requests
from requests_aws4auth import AWS4Auth
import boto3

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

def check_index_exists():
    """
    Check if the `restaurants` index exists in OpenSearch
    """
    url = f"{OPENSEARCH_HOST}/{INDEX_NAME}"
    headers = {"Content-Type": "application/json"}

    response = requests.head(url, auth=awsauth, headers=headers)

    if response.status_code == 200:
        print(f"Index `{INDEX_NAME}` exists.")
        return True
    elif response.status_code == 404:
        print(f"Index `{INDEX_NAME}` does not exist and needs to be created.")
        return False
    else:
        print(f"Failed to check index - Status Code: {response.status_code} - Response: {response.text}")
        return None

def create_index():
    """
    Check if the index exists and create it if it does not.
    """
    if check_index_exists():
        return {"statusCode": 200, "body": json.dumps(f"Index `{INDEX_NAME}` already exists, skipping creation.")}

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

    response = requests.put(url, auth=awsauth, json=index_settings, headers=headers)

    if response.status_code in [200, 201]:
        print("Index created successfully!")
        return {"statusCode": 200, "body": json.dumps(f"Index `{INDEX_NAME}` created successfully!")}
    else:
        print(f"Failed to create index - Status Code: {response.status_code}")
        print("Response:", response.text)
        return {"statusCode": response.status_code, "body": json.dumps(response.text)}

def fetch_all_documents():
    """
    Retrieve all documents from the OpenSearch `restaurants` index
    """
    url = f"{OPENSEARCH_HOST}/{INDEX_NAME}/_search"
    headers = {"Content-Type": "application/json"}
    query = {
        "size": 1000,  # Limit to 1000 results
        "query": {
            "match_all": {}  # Retrieve all data
        }
    }

    response = requests.get(url, auth=awsauth, json=query, headers=headers)

    if response.status_code == 200:
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        print(f"Successfully retrieved {len(hits)} documents.")
        
        # Extract `_source` field (actual stored documents)
        results = [hit["_source"] for hit in hits]
        
        return {"statusCode": 200, "body": json.dumps(results, indent=2)}
    else:
        print(f"Failed to retrieve documents - Status Code: {response.status_code}")
        print("Response:", response.text)
        return {"statusCode": response.status_code, "body": json.dumps(response.text)}

def lambda_handler(event, context):
    """
    Lambda entry point function
    """
    action = event.get("action", "query")  # Default to fetching data

    if action == "create_index":
        return create_index()
    elif action == "fetch_all":
        return fetch_all_documents()
    else:
        return {"statusCode": 400, "body": json.dumps("Invalid action, please provide 'create_index' or 'fetch_all'")}

