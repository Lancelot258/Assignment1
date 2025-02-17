import json
import boto3
import datetime
import requests
from decimal import Decimal
import time

# AWS Resources
dynamodb = boto3.resource('dynamodb', region_name='your-region')
table = dynamodb.Table('your-dynamodb-table')

# Yelp API Configuration
YELP_API_KEY = "your-yelp-api-key"
YELP_API_URL = "https://api.yelp.com/v3/businesses/search"

# Predefined restaurant types
valid_cuisines = ['italian', 'chinese', 'mexican', 'indian', 'american', 'japanese']

def fetch_yelp_restaurants(location, cuisine, total_required=240):
    """ Fetch restaurant data from Yelp API up to 240 restaurants (Yelp limit) """
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    restaurants = []
    seen_business_ids = set()
    limit_per_request = 50
    max_offset = 190  

    for offset in range(0, min(total_required, max_offset + limit_per_request), limit_per_request):
        if offset > max_offset:
            break  # Ensure offset does not exceed 190

        print(f"Fetching {cuisine} restaurants (Offset: {offset})...")
        params = {"location": location, "term": f"{cuisine} restaurants", "limit": limit_per_request, "offset": offset}
        response = requests.get(YELP_API_URL, headers=headers, params=params)

        if response.status_code == 200:
            batch = response.json().get("businesses", [])
            print(f"Received {len(batch)} results from Yelp (Offset: {offset})")

            for restaurant in batch:
                business_id = restaurant["id"]
                if business_id not in seen_business_ids:
                    seen_business_ids.add(business_id)
                    restaurants.append(restaurant)

            if len(batch) < limit_per_request:
                print(f"Yelp data insufficient for 240, stopping early. Retrieved {len(restaurants)} {cuisine} restaurants.")
                break  # Stop if Yelp data is insufficient
        else:
            print(f"Yelp API Error: {response.status_code} - {response.text}")
            break  

        time.sleep(1)

    print(f"Final count for {cuisine}: {len(restaurants)} restaurants.")
    return restaurants

def store_in_dynamodb(restaurants, cuisine):
    """ Use batch_writer() to store restaurant data in bulk """
    with table.batch_writer() as batch:
        for restaurant in restaurants:
            item = {
                "BusinessID": restaurant["id"],
                "Name": restaurant["name"],
                "Address": ", ".join(restaurant["location"]["display_address"]),
                "Cuisine": cuisine,
                "Coordinates": {
                    "latitude": Decimal(str(restaurant["coordinates"]["latitude"])),
                    "longitude": Decimal(str(restaurant["coordinates"]["longitude"]))
                },
                "NumberOfReviews": Decimal(str(restaurant["review_count"])),
                "Rating": Decimal(str(restaurant["rating"])),
                "ZipCode": restaurant["location"].get("zip_code", ""),
                "insertedAtTimestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            batch.put_item(Item=item)
    print(f"Batch inserted {len(restaurants)} {cuisine} restaurants into DynamoDB")

def lambda_handler(event, context):
    location = event.get("location", "New York")

    for cuisine in valid_cuisines:
        print(f"Fetching {cuisine} restaurants in {location}...")
        restaurants = fetch_yelp_restaurants(location, cuisine)
        if restaurants:
            store_in_dynamodb(restaurants, cuisine)

    return {"statusCode": 200, "body": json.dumps("Inserted all restaurants")}

