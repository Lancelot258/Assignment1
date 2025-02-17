import json
import logging
import boto3
from utils import *

# Set logging level
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize SQS client
sqs_client = boto3.client('sqs', region_name='your_region_name')

# SQS Queue URL
SQS_QUEUE_URL = "Your_SQS_URL"


def handle_dining_suggestions(intent_request):
    """Handles the dining recommendation logic."""
    logger.info(f"Received intent request: {json.dumps(intent_request, indent=2)}")

    # Retrieve `sessionState.intent` instead of `currentIntent`
    session_attributes = intent_request.get('sessionState', {}).get('sessionAttributes', {})
    intent = intent_request['sessionState']['intent']
    slots = intent['slots']

    # **Check if the request is in DialogCodeHook phase**
    if intent_request['invocationSource'] == 'DialogCodeHook':
        logger.info(" Entering DialogCodeHook phase")

        # **Check for missing slots and prompt user**
        for slot_name, slot_value in slots.items():
            logger.info(f" Checking Slot: {slot_name}, Current Value: {slot_value}")
            if slot_value is None:
                logger.info(f"Missing Slot: {slot_name}, triggering elicit_slot()")
                return elicit_slot(
                    session_attributes, 
                    intent['name'], 
                    slots, 
                    slot_name, 
                    f"Please provide {slot_name}."
                )

        # **Validate slot data**
        validation_result = validate_dining_suggestions(
            slots.get('Location'), slots.get('Cuisine'), slots.get('DiningTime'), 
            slots.get('NumberOfPeople'), slots.get('Email')
        )
        logger.info(f" Slot validation result: {validation_result}")

        if not validation_result['isValid']:
            logger.info(f" Invalid Slot {validation_result['violatedSlot']}, triggering elicit_slot()")
            return elicit_slot(
                session_attributes, 
                intent['name'], 
                slots, 
                validation_result['violatedSlot'], 
                validation_result['message']['content']
            )

        # **All slots are valid, delegate processing to Lex**
        logger.info(" All slots are filled, calling delegate()")
        # return delegate(session_attributes, slots)

    # **Extract slot values**
    location = get_slot_value(slots.get('Location'))
    cuisine = get_slot_value(slots.get('Cuisine'))
    dining_time = get_slot_value(slots.get('DiningTime'))
    number_of_people = get_slot_value(slots.get('NumberOfPeople'))
    email = get_slot_value(slots.get('Email'))

    # **Check if all slots are filled**
    if None in [location, cuisine, dining_time, number_of_people, email]:
        missing_slot = "Location" if location is None else \
                       "Cuisine" if cuisine is None else \
                       "DiningTime" if dining_time is None else \
                       "NumberOfPeople" if number_of_people is None else "Email"
        logger.info(f"Missing Slot: {missing_slot}, continuing ElicitSlot()")

        return elicit_slot(
            session_attributes, 
            intent['name'], 
            slots, 
            missing_slot, 
            f"Please provide {missing_slot}."
        )

    # **All slots are filled, prepare to push to SQS**
    sqs_message = {
        "location": location,
        "cuisine": cuisine,
        "dining_time": dining_time,
        "number_of_people": number_of_people,
        "email": email
    }

    try:
        sqs_response = sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(sqs_message, ensure_ascii=False)
        )
        logger.info(f" SQS message successfully sent, Message ID: {sqs_response['MessageId']}")

        # **Return Fulfilled response**
        message = (
            f"Based on your request, here are some {cuisine} restaurant recommendations in {location} "
            f"for {number_of_people} people at {dining_time}. "
            f"We will send detailed information to {email}."
        )

        return close(session_attributes, "Fulfilled", message)

    except Exception as e:
        logger.error(f" SQS message sending failed: {str(e)}")

        return close(session_attributes, "Failed", "Booking failed, please try again later.")


def lambda_handler(event, context):
    """Lambda entry point."""
    logger.info(" Received event: %s", json.dumps(event, indent=2))

    # Get Intent Name
    intent_name = event['sessionState']['intent']['name']

    if intent_name == "DiningSuggestionsIntent":
        return handle_dining_suggestions(event)
    
    else:
        logger.info(f"Unhandled Intent: {intent_name}")
        return {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {"name": intent_name, "state": "Fulfilled"}
            },
            "messages": [{"contentType": "PlainText", "content": "I'm not sure how to handle that request."}]
        }

