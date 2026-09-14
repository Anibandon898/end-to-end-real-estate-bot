from fastapi import APIRouter
from pydantic import BaseModel
import re

from backend.models.lead import Lead
from backend.services.n8n_service import send_lead_to_n8n


router = APIRouter(
    prefix="/api/v1",
    tags=["Leads"]
)


# Temporary in-memory conversation storage
conversations = {}


@router.post("/leads")
def create_lead(lead: Lead):
    lead_data = lead.model_dump()

    response = send_lead_to_n8n(lead_data)

    return {
        "success": True,
        "message": "Lead received and sent to n8n successfully",
        "n8n_status": response.status_code,
        "lead": lead_data
    }


class ChatMessage(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
def chat(message: ChatMessage):

    session_id = message.session_id
    user_message = message.message.strip()

    # CREATE NEW CONVERSATION
    if session_id not in conversations:
        conversations[session_id] = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "property_type": "",
            "purpose": "",
            "budget": "",
            "bedrooms": "",
            "timeline": "",
            "message": ""
        }

    conversation = conversations[session_id]

    if not user_message:
        return {
            "reply": "Please enter a message."
        }

    text = user_message.lower()

    # NAME
    if not conversation["name"]:
        name_match = re.search(
            r"(?:my name is|i am|i'm|name is)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})",
            user_message,
            re.IGNORECASE
        )

        if name_match:
            conversation["name"] = name_match.group(1).strip()

    # EMAIL
    if not conversation["email"]:
        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            user_message
        )

        if email_match:
            conversation["email"] = email_match.group(0)

    # PHONE
    if not conversation["phone"]:
        cleaned_phone_text = (
            user_message
            .replace(" ", "")
            .replace("-", "")
        )

        phone_match = re.search(
            r"(?:\+234|0)\d{10}\b",
            cleaned_phone_text
        )

        if phone_match:
            conversation["phone"] = phone_match.group(0)

    # PROPERTY TYPE
    if any(word in text for word in [
        "house",
        "home",
        "bungalow",
        "duplex"
    ]):
        conversation["property_type"] = "house"

    elif any(word in text for word in [
        "apartment",
        "flat"
    ]):
        conversation["property_type"] = "apartment"

    elif any(word in text for word in [
        "land",
        "plot"
    ]):
        conversation["property_type"] = "land"

    elif any(word in text for word in [
        "office",
        "shop",
        "commercial"
    ]):
        conversation["property_type"] = "commercial property"

    # PURPOSE
    if any(word in text for word in [
        "buy",
        "buying",
        "purchase"
    ]):
        conversation["purpose"] = "buying"

    elif any(word in text for word in [
        "rent",
        "renting",
        "lease"
    ]):
        conversation["purpose"] = "renting"

    # LOCATION
    if "uyo" in text:
        conversation["location"] = "Uyo"

    elif "lagos" in text:
        conversation["location"] = "Lagos"

    elif "abuja" in text:
        conversation["location"] = "Abuja"

    # BEDROOMS
    bedroom_match = re.search(
        r"(\d+)\s*(?:bedroom|bedrooms|bed|beds)",
        text
    )

    if bedroom_match:
        conversation["bedrooms"] = bedroom_match.group(1)

    # BUDGET
    # IMPORTANT:
    # Only extract a budget when the message contains
    # an explicit budget or currency indicator.
    #
    # This prevents:
    # "Within 3 months"
    # from becoming:
    # "3 million"

    budget_match = None

    if (
        "budget" in text
        or "₦" in user_message
        or re.search(
            r"(?<![a-z])ngn\s*[\d,]",
            text,
            re.IGNORECASE
        )
        or re.search(
            r"₦\s*[\d,]",
            user_message,
            re.IGNORECASE
        )
    ):

        budget_match = re.search(
            r"(?:"
            r"budget\s*(?:is|of)?\s*"
            r"|₦\s*"
            r"|(?<![a-z])ngn\s*"
            r")"
            r"([\d,]+(?:\.\d+)?)"
            r"\s*"
            r"(million|m|billion|b)?",
            text,
            re.IGNORECASE
        )

    if budget_match:

        amount = budget_match.group(1).replace(",", "")
        multiplier = budget_match.group(2)

        budget = float(amount)

        if multiplier:

            multiplier = multiplier.lower()

            if multiplier in [
                "million",
                "m"
            ]:
                budget *= 1_000_000

            elif multiplier in [
                "billion",
                "b"
            ]:
                budget *= 1_000_000_000

        conversation["budget"] = str(int(budget))

    # TIMELINE
    timeline_patterns = [
        "immediately",
        "right away",
        "asap",
        "this week",
        "next week",
        "this month",
        "next month",
        "1 month",
        "2 months",
        "3 months",
        "4 months",
        "5 months",
        "6 months",
        "one month",
        "two months",
        "three months",
        "four months",
        "five months",
        "six months",
        "within a month",
        "within two months",
        "within three months",
        "within six months"
    ]

    if any(pattern in text for pattern in timeline_patterns):
        conversation["timeline"] = user_message

    # SAVE INITIAL PROPERTY MESSAGE ONLY
    if not conversation["message"]:

        if (
            conversation["property_type"]
            or conversation["location"]
            or conversation["purpose"]
            or conversation["budget"]
            or conversation["bedrooms"]
        ):
            conversation["message"] = user_message

    # ASK FOR PROPERTY TYPE
    if not conversation["property_type"]:

        return {
            "reply": (
                "I'd be happy to help you find a property. "
                "What type of property are you looking for? "
                "For example: house, apartment, land, or office."
            )
        }

    # ASK FOR LOCATION
    if not conversation["location"]:

        return {
            "reply": (
                f"Great! I can help you find a "
                f"{conversation['property_type']}. "
                "Which location are you interested in?"
            )
        }

    # ASK FOR PURPOSE
    if not conversation["purpose"]:

        return {
            "reply": (
                f"Great! You are looking for a "
                f"{conversation['property_type']} in "
                f"{conversation['location']}. "
                "Are you looking to buy or rent?"
            )
        }

    # ASK FOR BUDGET
    if not conversation["budget"]:

        return {
            "reply": "What is your budget for the property?"
        }

    # ASK FOR BEDROOMS
    if (
        not conversation["bedrooms"]
        and conversation["property_type"] in [
            "house",
            "apartment"
        ]
    ):

        return {
            "reply": "How many bedrooms do you need?"
        }

    # ASK FOR NAME
    if not conversation["name"]:

        return {
            "reply": (
                "Great! I have your property requirements. "
                "May I have your full name?"
            )
        }

    # ASK FOR EMAIL
    if not conversation["email"]:

        return {
            "reply": (
                f"Thanks, {conversation['name']}. "
                "What is your email address?"
            )
        }

    # ASK FOR PHONE
    if not conversation["phone"]:

        return {
            "reply": (
                "What is the best phone number to reach you?"
            )
        }

    # ASK FOR TIMELINE
    if not conversation["timeline"]:

        return {
            "reply": (
                "When are you planning to buy or rent the property? "
                "For example: immediately, within 3 months, "
                "or within 6 months."
            )
        }

    # COMPLETE CONVERSATION
    return {
        "reply": (
            "Perfect! I now have all the information I need. "
            "Thank you. Our property team can follow up with you shortly."
        ),
        "conversation": conversation
    }