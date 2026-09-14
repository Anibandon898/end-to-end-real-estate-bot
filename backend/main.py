import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="PropertyPilot AI",
    version="1.0.0",
    description="Smart Real Estate Assistant"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CONFIG
# =========================================================

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/real-estate"
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SUPABASE_TABLE = "Real estate lead"


# =========================================================
# SESSION STORAGE
# =========================================================

sessions = {}


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


class LeadRequest(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    property_type: str = ""
    purpose: str = ""
    budget: str = ""
    bedrooms: Optional[int] = None
    timeline: str = ""
    message: str = ""
    lead_quality: str = ""
    main_problem: str = ""
    recommended_action: str = ""
    source: str = "real-estate-chatbot"


# =========================================================
# BASIC ROUTES
# =========================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "PropertyPilot AI is running"
    }


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "service": "propertypilot-ai"
    }


# =========================================================
# EXTRACTION
# =========================================================

def extract_email(text: str) -> str:
    match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text
    )

    return match.group(0).lower() if match else ""


def extract_phone(text: str) -> str:
    cleaned = re.sub(r"[\s().-]", "", text)

    match = re.search(
        r"(?<!\d)(?:\+234|234|0)[7-9]\d{9}(?!\d)",
        cleaned
    )

    if not match:
        return ""

    phone = match.group(0)

    if phone.startswith("234"):
        return "+234" + phone[3:]

    return phone


def extract_name(text: str) -> str:
    patterns = [
        r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,50})",
        r"\bi'm called\s+([A-Za-z][A-Za-z .'-]{1,50})",
        r"\bi am called\s+([A-Za-z][A-Za-z .'-]{1,50})",
        r"\bcall me\s+([A-Za-z][A-Za-z .'-]{1,50})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            name = match.group(1).strip()

            name = re.split(
                r"\b(?:and|my|phone|email|number)\b",
                name,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0].strip()

            if name:
                return name.title()

    return ""


def extract_purpose(text: str) -> str:
    text = text.lower()

    if re.search(r"\b(buy|buying|purchase|purchasing|own)\b", text):
        return "Buying"

    if re.search(r"\b(rent|renting|lease|leasing)\b", text):
        return "Renting"

    if re.search(r"\b(invest|investing|investment)\b", text):
        return "Investment"

    return ""


def extract_property_type(text: str) -> str:
    text = text.lower()

    property_types = {
        "house": "House",
        "home": "House",
        "apartment": "Apartment",
        "flat": "Flat",
        "duplex": "Duplex",
        "land": "Land",
        "shop": "Shop",
        "office": "Office",
        "warehouse": "Warehouse",
        "bungalow": "Bungalow",
        "commercial": "Commercial"
    }

    for key, value in property_types.items():
        if re.search(rf"\b{re.escape(key)}\b", text):
            return value

    return ""


def extract_location(text: str) -> str:
    locations = [
        "Uyo",
        "Ikot Ekpene",
        "Eket",
        "Oron",
        "Akwa Ibom",
        "Lagos",
        "Abuja",
        "Port Harcourt",
        "Calabar",
        "Ibadan",
        "Enugu",
        "Benin",
        "Warri",
        "Lekki",
        "Ikeja",
        "Ajah",
        "Victoria Island"
    ]

    text_lower = text.lower()

    for location in locations:
        if location.lower() in text_lower:
            return location

    return ""


def extract_budget(text: str) -> str:

    phone = extract_phone(text)

    if phone:
        text = text.replace(phone, " ")

    match = re.search(
        r"(?:₦|ngn|n)?\s*"
        r"([\d]+(?:[.,]\d+)?)"
        r"\s*"
        r"(billion|million|bn|b|m)?\b",
        text.lower()
    )

    if not match:
        return ""

    number = match.group(1).replace(",", "")
    unit = match.group(2)

    try:
        value = float(number)

        if unit in ["million", "m"]:
            value *= 1_000_000

        elif unit in ["billion", "bn", "b"]:
            value *= 1_000_000_000

        elif value < 10000:
            return ""

        return f"₦{value:,.0f}"

    except ValueError:
        return ""


def budget_number(budget: str):
    if not budget:
        return None

    value = re.sub(r"[^\d.]", "", budget)

    if not value:
        return None

    try:
        number = float(value)

        return int(number) if number.is_integer() else number

    except ValueError:
        return None


def extract_bedrooms(text: str) -> Optional[int]:
    match = re.search(
        r"\b(\d+)\s*(?:bedrooms?|beds?|br)\b",
        text,
        re.IGNORECASE
    )

    return int(match.group(1)) if match else None


def extract_timeline(text: str) -> str:

    text_lower = text.lower().strip()

    if any(
        phrase in text_lower
        for phrase in [
            "immediately",
            "as soon as possible",
            "right away",
            "now",
            "this week"
        ]
    ):
        return "Immediately"

    match = re.search(
        r"\b(\d+)\s*"
        r"(day|days|week|weeks|month|months|year|years)\b",
        text_lower
    )

    if match:
        return f"{match.group(1)} {match.group(2)}"

    return ""


# =========================================================
# SESSION
# =========================================================

def new_session(session_id: str):

    if session_id not in sessions:

        sessions[session_id] = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "property_type": "",
            "purpose": "",
            "budget": "",
            "bedrooms": None,
            "timeline": "",
            "message": "",
            "lead_quality": "COLD",
            "main_problem": "",
            "recommended_action": "",
            "source": "real-estate-chatbot",
            "conversation_started": datetime.utcnow().isoformat(),
            "last_message": "",
            "n8n_sent": False,
            "supabase_saved": False,
            "started": False
        }

    return sessions[session_id]


# =========================================================
# LEAD QUALITY
# =========================================================

def calculate_quality(lead):

    fields = [
        "location",
        "property_type",
        "purpose",
        "budget",
        "timeline"
    ]

    score = sum(
        1 for field in fields
        if lead.get(field)
    )

    if score == 5:
        return "HOT"

    if score >= 3:
        return "WARM"

    return "COLD"


def update_quality(lead):

    lead["lead_quality"] = calculate_quality(lead)

    if lead["purpose"] == "Buying":
        lead["main_problem"] = "Customer wants to buy a property."

    elif lead["purpose"] == "Renting":
        lead["main_problem"] = "Customer is looking for a property to rent."

    elif lead["purpose"] == "Investment":
        lead["main_problem"] = "Customer is interested in property investment."

    else:
        lead["main_problem"] = (
            "Customer has not provided enough "
            "property requirements yet."
        )

    if lead["lead_quality"] == "HOT":

        lead["recommended_action"] = (
            "Contact immediately and provide "
            "suitable property options."
        )

    elif lead["lead_quality"] == "WARM":

        lead["recommended_action"] = (
            "Continue the conversation and collect "
            "the remaining requirements."
        )

    else:

        lead["recommended_action"] = (
            "Continue nurturing the customer and "
            "collect more property requirements."
        )


# =========================================================
# UPDATE DATA
# =========================================================

def update_lead(lead, message):

    lead["last_message"] = message

    email = extract_email(message)
    phone = extract_phone(message)
    name = extract_name(message)

    purpose = extract_purpose(message)
    location = extract_location(message)
    property_type = extract_property_type(message)
    budget = extract_budget(message)
    bedrooms = extract_bedrooms(message)
    timeline = extract_timeline(message)

    if email:
        lead["email"] = email

    if phone:
        lead["phone"] = phone

    if name:
        lead["name"] = name

    if purpose:
        lead["purpose"] = purpose

    if location:
        lead["location"] = location

    if property_type:
        lead["property_type"] = property_type

    if budget:
        lead["budget"] = budget

    if bedrooms is not None:
        lead["bedrooms"] = bedrooms

    if timeline:
        lead["timeline"] = timeline

    # Store only genuine additional comments
    if (
        not email
        and not phone
        and not name
        and not purpose
        and not location
        and not property_type
        and not budget
        and not bedrooms
        and not timeline
    ):
        lead["message"] = message

    update_quality(lead)


# =========================================================
# NEXT QUESTION
# =========================================================

def next_question(lead):

    if not lead["name"]:
        return "May I have your name?", "name"

    if not lead["email"]:
        return "What is your email address?", "email"

    if not lead["phone"]:
        return "What is the best phone number to reach you?", "phone"

    if not lead["purpose"]:
        return "Are you looking to buy, rent, or invest?", "purpose"

    if not lead["location"]:
        return "Which location or area are you interested in?", "location"

    if not lead["property_type"]:
        return "What type of property are you looking for?", "property_type"

    if not lead["budget"]:
        return "What is your budget?", "budget"

    if not lead["timeline"]:
        return "When are you planning to get the property?", "timeline"

    return "", ""


# =========================================================
# N8N
# =========================================================

def send_to_n8n(lead):

    if lead["n8n_sent"]:
        return {
            "sent": True,
            "status": "already_sent"
        }

    payload = {
        "name": lead["name"],
        "email": lead["email"],
        "phone": lead["phone"],
        "location": lead["location"],
        "property_type": lead["property_type"],
        "purpose": lead["purpose"],
        "budget": budget_number(lead["budget"]),
        "bedrooms": lead["bedrooms"],
        "timeline": lead["timeline"],
        "message": lead["message"],
        "lead_quality": lead["lead_quality"],
        "main_problem": lead["main_problem"],
        "recommended_action": lead["recommended_action"],
        "source": "real-estate-webhook"
    }

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=15
        )

        if 200 <= response.status_code < 300:

            lead["n8n_sent"] = True

            return {
                "sent": True,
                "status_code": response.status_code
            }

        return {
            "sent": False,
            "status_code": response.status_code,
            "error": response.text[:500]
        }

    except Exception as error:

        return {
            "sent": False,
            "error": str(error)
        }


# =========================================================
# SUPABASE
# =========================================================

def save_to_supabase(lead):

    if lead["supabase_saved"]:
        return {
            "saved": True,
            "status": "already_saved"
        }

    if not SUPABASE_URL or not SUPABASE_KEY:

        return {
            "saved": False,
            "error": "Supabase environment variables are not configured"
        }

    table = quote(
        SUPABASE_TABLE,
        safe=""
    )

    url = (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    payload = {
        "name": lead["name"],
        "email": lead["email"],
        "phone": lead["phone"],
        "location": lead["location"],
        "property_type": lead["property_type"],
        "purpose": lead["purpose"],
        "budget": budget_number(lead["budget"]),
        "timeline": lead["timeline"],
        "message": lead["message"],
        "lead_quality": lead["lead_quality"],
        "main_problem": lead["main_problem"],
        "recommended_action": lead["recommended_action"],
        "source": "real-estate-chatbot"
    }

    if lead["bedrooms"] is not None:
        payload["bedroom"] = lead["bedrooms"]

    try:

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )

        if 200 <= response.status_code < 300:

            lead["supabase_saved"] = True

            return {
                "saved": True,
                "status_code": response.status_code
            }

        return {
            "saved": False,
            "status_code": response.status_code,
            "error": response.text[:1000]
        }

    except Exception as error:

        return {
            "saved": False,
            "error": str(error)
        }


# =========================================================
# CHAT
# =========================================================

@app.post("/api/v1/chat")
def chat(request: ChatRequest):

    session_id = request.session_id.strip()
    message = request.message.strip()

    if not session_id:
        return {
            "success": False,
            "error": "session_id is required"
        }

    if not message:
        return {
            "success": False,
            "error": "message is required"
        }

    lead = new_session(session_id)

    # =====================================================
    # FIRST MESSAGE
    # =====================================================

    if not lead["started"]:

        lead["started"] = True
        lead["last_message"] = message

        # If the first message already contains a name,
        # capture it. Otherwise ask for name.
        name = extract_name(message)

        if name:
            lead["name"] = name
            update_quality(lead)

            reply = "What is your email address?"
            missing_field = "email"

        else:

            reply = "Welcome! I'm your real estate assistant. May I have your name?"
            missing_field = "name"

        return build_response(
            session_id,
            lead,
            reply,
            missing_field,
            False
        )

    # =====================================================
    # PROCESS MESSAGE
    # =====================================================

    update_lead(
        lead,
        message
    )

    # =====================================================
    # FIND NEXT QUESTION
    # =====================================================

    reply, missing_field = next_question(lead)

    # =====================================================
    # COMPLETE
    # =====================================================

    if not missing_field:

        n8n_result = send_to_n8n(lead)

        supabase_result = save_to_supabase(lead)

        return build_response(
            session_id,
            lead,
            (
                "Thank you! I have all the information I need. "
                "Your property request has been received successfully. "
                "Our team will contact you shortly."
            ),
            "",
            True,
            n8n_result,
            supabase_result
        )

    # =====================================================
    # CONTINUE
    # =====================================================

    return build_response(
        session_id,
        lead,
        reply,
        missing_field,
        False
    )


# =========================================================
# RESPONSE BUILDER
# =========================================================

def build_response(
    session_id,
    lead,
    reply,
    missing_field,
    completed,
    n8n_result=None,
    supabase_result=None
):

    if n8n_result is None:
        n8n_result = {
            "sent": lead["n8n_sent"]
        }

    if supabase_result is None:
        supabase_result = {
            "saved": lead["supabase_saved"]
        }

    return {
        "success": True,
        "session_id": session_id,
        "reply": reply,
        "lead_quality": lead["lead_quality"],
        "completed": completed,
        "missing_field": missing_field,
        "collected_data": {
            "name": lead["name"],
            "email": lead["email"],
            "phone": lead["phone"],
            "location": lead["location"],
            "property_type": lead["property_type"],
            "purpose": lead["purpose"],
            "budget": lead["budget"],
            "bedrooms": lead["bedrooms"],
            "timeline": lead["timeline"],
            "message": lead["message"],
            "lead_quality": lead["lead_quality"],
            "main_problem": lead["main_problem"],
            "recommended_action": lead["recommended_action"],
            "source": lead["source"],
            "conversation_started": lead["conversation_started"],
            "last_message": lead["last_message"]
        },
        "integrations": {
            "n8n": n8n_result,
            "supabase": supabase_result
        }
    }


# =========================================================
# MANUAL LEAD
# =========================================================

@app.post("/api/v1/leads")
def create_lead(request: LeadRequest):

    lead = request.model_dump()

    lead["n8n_sent"] = False
    lead["supabase_saved"] = False

    update_quality(lead)

    n8n_result = send_to_n8n(lead)
    supabase_result = save_to_supabase(lead)

    return {
        "success": True,
        "message": "Lead processed successfully",
        "lead": lead,
        "integrations": {
            "n8n": n8n_result,
            "supabase": supabase_result
        }
    }


# =========================================================
# GET SESSION
# =========================================================

@app.get("/api/v1/sessions/{session_id}")
def get_session(session_id: str):

    if session_id not in sessions:

        return {
            "success": False,
            "message": "Session not found"
        }

    return {
        "success": True,
        "session_id": session_id,
        "lead": sessions[session_id]
    }