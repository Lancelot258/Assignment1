import datetime

# --- Lex Response Helper Functions ---

def get_slot_value(slot):
    """Extract interpretedValue from Lex V2 Slot structure"""
    if isinstance(slot, dict) and "value" in slot:
        return slot["value"].get("interpretedValue", None)
    elif isinstance(slot, str):
        return slot
    return None


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """Request user input for a specific Slot (Lex V2 structure)"""
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": slot_to_elicit
            },
            "sessionAttributes": session_attributes,
            "intent": {
                "name": intent_name,
                "slots": slots,
                "state": "InProgress"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message
            }
        ]
    }


def close(session_attributes, fulfillment_state, message):
    """End conversation (Lex V2 structure)"""
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "sessionAttributes": session_attributes,
            "intent": {
                "name": "DiningSuggestionsIntent",
                "state": fulfillment_state
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message
            }
        ]
    }


def build_validation_result(is_valid, violated_slot, message_content):
    """Build slot validation result"""
    if not is_valid:
        return {
            "isValid": False,
            "violatedSlot": violated_slot,
            "message": {"contentType": "PlainText", "content": message_content}
        }
    return {"isValid": True}

# --- Slot Validation Functions ---
def is_valid_location(location):
    """Check if the city is within the supported locations"""
    valid_locations = ['new york', 'seattle', 'san francisco', 'chicago', 'boston', 'miami']

    if isinstance(location, dict):  # Handle Lex V2 Slot structure
        location = location.get("value", {}).get("interpretedValue", "")

    return location.lower() in valid_locations if isinstance(location, str) else False


def is_valid_cuisine(cuisine):
    """Check if the cuisine type is valid"""
    valid_cuisines = ['italian', 'chinese', 'mexican', 'indian', 'american', 'japanese']

    if isinstance(cuisine, dict):  # Handle Lex V2 Slot structure
        cuisine = cuisine.get("value", {}).get("interpretedValue", "")

    return cuisine.lower() in valid_cuisines if isinstance(cuisine, str) else False


def is_valid_dining_time(dining_time):
    """Check if the dining time follows Amazon Lex's amazon.time format"""
    try:
        formats = ['%H:%M', '%I:%M %p']
        for fmt in formats:
            try:
                datetime.datetime.strptime(dining_time, fmt).time()
                return True, None
            except ValueError:
                continue
        return False, "The dining time format is invalid. Please use HH:MM (24-hour) or H:MM AM/PM format."
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"


def is_valid_number_of_people(number_of_people):
    """Check if the number of people is reasonable"""
    try:
        number_of_people = int(number_of_people)
        if number_of_people <= 0:
            return False, "The number of people should be a positive integer. Please provide a valid number."
        if number_of_people > 20:
            return False, "We do not support bookings for more than 20 people. Please enter a smaller number."
        return True, None
    except ValueError:
        return False, "The number of people should be a valid integer."

# --- Main Validation Function ---
def validate_dining_suggestions(location, cuisine, dining_time, number_of_people, email):
    """Perform all slot-related validations"""

    location = get_slot_value(location)
    cuisine = get_slot_value(cuisine)  
    dining_time = get_slot_value(dining_time)
    number_of_people = get_slot_value(number_of_people)
    email = get_slot_value(email)

    if location and not is_valid_location(location):
        return build_validation_result(False, 'Location', f"We do not support {location}. Please choose from: New York, Seattle, San Francisco, Chicago, Boston, Los Angeles, Houston, or Miami.")

    if cuisine and not is_valid_cuisine(cuisine):
        return build_validation_result(False, 'Cuisine', "We only support Italian, Chinese, Mexican, Indian, American, or Japanese cuisines.")

    if dining_time:
        dining_time_valid, dining_time_message = is_valid_dining_time(dining_time)
        if not dining_time_valid:
            return build_validation_result(False, 'DiningTime', dining_time_message)

    if number_of_people:
        number_of_people_valid, number_of_people_message = is_valid_number_of_people(number_of_people)
        if not number_of_people_valid:
            return build_validation_result(False, 'NumberOfPeople', number_of_people_message)

    return {"isValid": True, "violatedSlot": None, "message": None}


