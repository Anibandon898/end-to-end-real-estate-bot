import os
import re
from datetime import datetime
from typing import Optional

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr


# =========================================================
# PROPERTY PILOT AI
# CLEAN REAL ESTATE CHATBOT BACKEND
# =========================================================

app = FastAPI(
    title="PropertyPilot AI",
    description="Smart Real Estate Assistant",
    version="2.0.0",
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
# CONFIGURATION
# =========================================================

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/real-estate",
)

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "",
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "",
)


# =========================================================
# NIGERIAN STATES + FCT
# =========================================================

NIGERIAN_STATES = {
    "abia",
    "adamawa",
    "akwa ibom",
    "anambra",
    "bauchi",
    "bayelsa",
    "benue",
    "borno",
    "cross river",
    "delta",
    "ebonyi",
    "edo",
    "ekiti",
    "enugu",
    "gombe",
    "imo",
    "jigawa",
    "kaduna",
    "kano",
    "katsina",
    "kebbi",
    "kogi",
    "kwara",
    "lagos",
    "nasarawa",
    "niger",
    "ogun",
    "ondo",
    "osun",
    "oyo",
    "plateau",
    "rivers",
    "sokoto",
    "taraba",
    "yobe",
    "zamfara",
    "fct",
    "abuja",
}


# =========================================================
# NIGERIAN LOCATIONS
# =========================================================

NIGERIAN_LOCATIONS = {
    "abuja",
    "uyo",
    "ikot ekpene",
    "eket",
    "oron",
    "ikono",
    "etinan",
    "ibiono",
    "itu",
    "mkpat enin",
    "eastern obolo",
    "lagos",
    "lekki",
    "ikeja",
    "yaba",
    "surulere",
    "ikoyi",
    "victoria island",
    "vi",
    "ajah",
    "badagry",
    "apapa",
    "festac",
    "maryland",
    "magodo",
    "ogba",
    "ikeja gra",
    "banana island",
    "ikorodu",
    "ikorodu town",
    "epe",
    "oshodi",
    "mushin",
    "agege",
    "alimosho",
    "ibadan",
    "enugu",
    "nsukka",
    "port harcourt",
    "ph",
    "benin city",
    "benin",
    "warri",
    "asaba",
    "calabar",
    "owerri",
    "aba",
    "umuahia",
    "onitsha",
    "awka",
    "nnewi",
    "makurdi",
    "jos",
    "kaduna",
    "zaria",
    "kano",
    "katsina",
    "sokoto",
    "maiduguri",
    "yola",
    "bauchi",
    "gombe",
    "jalingo",
    "ilorin",
    "akure",
    "ondo",
    "ado ekiti",
    "osogbo",
    "oshogbo",
    "abeokuta",
    "sagamu",
    "ijebu ode",
    "minna",
    "lokoja",
    "lafia",
    "birnin kebbi",
    "gusau",
    "damaturu",
    "abakaliki",
    "oshogbo",
    "uyo",
}


# =========================================================
# PROPERTY TYPES
# =========================================================

PROPERTY_TYPES = {
    "house": "House",
    "home": "House",
    "apartment": "Apartment",
    "flat": "Apartment",
    "duplex": "Duplex",
    "bungalow": "Bungalow",
    "terrace": "Terrace",
    "terraced": "Terrace",
    "land": "Land",
    "plot": "Land",
    "commercial": "Commercial",
    "office": "Commercial",
    "shop": "Commercial",
    "warehouse": "Commercial",
    "hotel": "Hotel",
    "estate": "Estate",
}


# =========================================================
# PURPOSES
# =========================================================

PURPOSES = {
    "buy": "Buying",
    "buying": "Buying",
    "purchase": "Buying",
    "purchasing": "Buying",

    "rent": "Renting",
    "renting": "Renting",
    "lease": "Renting",
    "leasing": "Renting",

    "invest": "Investment",
    "investing": "Investment",
    "investment": "Investment",
}


# =========================================================
# MODELS
# =========================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


class LeadRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    purpose: Optional[str] = None
    budget: Optional[float] = None
    bedrooms: Optional[int] = None
    timeline: Optional[str] = None
    message: Optional[str] = None
    lead_quality: Optional[str] = None
    main_problem: Optional[str] = None
    recommended_action: Optional[str] = None
    source: str = "real-estate-chatbot"
    property_images: Optional[list] = None


# =========================================================
# SESSION STORAGE
# =========================================================

sessions = {}


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def normalize(value: str) -> str:
    return clean_text(value).lower()


# =========================================================
# EMAIL EXTRACTION
# =========================================================

def extract_email(message: str) -> Optional[str]:

    match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        message,
        re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


# =========================================================
# PHONE EXTRACTION
# =========================================================

def extract_phone(message: str) -> Optional[str]:

    text = clean_text(message)

    # -----------------------------------------------------
    # INTERNATIONAL NUMBERS
    #
    # Examples:
    # +44 7911 123456
    # +1 202 555 0147
    # +971 50 123 4567
    # +27 82 123 4567
    # +33 6 12 34 56 78
    # +49 151 12345678
    # -----------------------------------------------------

    international_matches = re.findall(
        r"(?<!\w)"
        r"\+\d{1,4}"
        r"(?:[\s().-]*\d){7,15}"
        r"(?!\w)",
        text,
    )

    for raw_phone in international_matches:

        phone = re.sub(
            r"[\s().-]",
            "",
            raw_phone,
        )

        digits = phone[1:]

        if 8 <= len(digits) <= 15:
            return phone

    # -----------------------------------------------------
    # NIGERIAN LOCAL NUMBERS
    #
    # 08031234567
    # 07012345678
    # 08123456789
    # -----------------------------------------------------

    nigeria_local = re.search(
        r"(?<!\w)"
        r"(0[789]\d{9})"
        r"(?!\w)",
        text,
    )

    if nigeria_local:

        local_number = nigeria_local.group(1)

        return "+234" + local_number[1:]

    # -----------------------------------------------------
    # NIGERIAN FORMATTED NUMBERS
    #
    # 0803 123 4567
    # 0803-123-4567
    # 0803.123.4567
    # -----------------------------------------------------

    nigeria_formatted = re.search(
        r"(?<!\w)"
        r"(0[789]\d{2})"
        r"[\s.-]+"
        r"(\d{3})"
        r"[\s.-]+"
        r"(\d{4})"
        r"(?!\w)",
        text,
    )

    if nigeria_formatted:

        local_number = (
            nigeria_formatted.group(1)
            + nigeria_formatted.group(2)
            + nigeria_formatted.group(3)
        )

        return "+234" + local_number[1:]

    return None


# =========================================================
# REMOVE PHONE NUMBERS FROM TEXT
# =========================================================

def remove_phone_numbers(text: str) -> str:

    result = text

    # International
    result = re.sub(
        r"(?<!\w)"
        r"\+\d{1,4}"
        r"(?:[\s().-]*\d){7,15}"
        r"(?!\w)",
        " ",
        result,
    )

    # Nigerian local / formatted
    result = re.sub(
        r"(?<!\w)"
        r"0[789]\d{2}"
        r"(?:[\s.-]?\d{3})"
        r"(?:[\s.-]?\d{4})"
        r"(?!\w)",
        " ",
        result,
    )

    return clean_text(result)


# =========================================================
# NAME EXTRACTION
# =========================================================

def extract_name(message: str) -> Optional[str]:

    text = clean_text(message)

    if not text:
        return None

    # -----------------------------------------------------
    # Explicit introductions
    # -----------------------------------------------------

    explicit_patterns = [
        r"^(?:my name is)\s+(.+)$",
        r"^(?:i am)\s+(.+)$",
        r"^(?:i'm)\s+(.+)$",
        r"^(?:this is)\s+(.+)$",
        r"^(?:call me)\s+(.+)$",
        r"^(?:you can call me)\s+(.+)$",
    ]

    for pattern in explicit_patterns:

        match = re.match(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            candidate = clean_text(
                match.group(1)
            )

            candidate = re.sub(
                r"[.!?,]+$",
                "",
                candidate,
            )

            if candidate:
                return candidate

    # -----------------------------------------------------
    # Standalone names
    # -----------------------------------------------------

    candidate = text.strip(
        " .,!?:;"
    )

    lower = candidate.lower()

    blocked = {
        "yes",
        "no",
        "okay",
        "ok",
        "house",
        "home",
        "apartment",
        "flat",
        "duplex",
        "bungalow",
        "land",
        "plot",
        "commercial",
        "office",
        "shop",
        "buy",
        "buying",
        "rent",
        "renting",
        "investment",
        "invest",
        "investing",
        "abuja",
        "lagos",
        "uyo",
        "kaduna",
        "kano",
        "ibadan",
        "enugu",
        "calabar",
        "owerri",
        "port harcourt",
        "benin",
    }

    if lower in blocked:
        return None

    # Do not interpret a sentence as a name.
    sentence_words = {
        "i",
        "want",
        "need",
        "looking",
        "for",
        "a",
        "an",
        "the",
        "house",
        "home",
        "property",
        "in",
        "at",
        "near",
        "around",
        "buy",
        "rent",
    }

    candidate_words = lower.split()

    if any(
        word in sentence_words
        for word in candidate_words
    ):
        return None

    # No maximum name length.
    if re.fullmatch(
        r"[A-Za-zÀ-ÖØ-öø-ÿ'’\-]+"
        r"(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ'’\-]+)*",
        candidate,
    ):
        return candidate

    return None


# =========================================================
# PURPOSE EXTRACTION
# =========================================================

def extract_purpose(message: str) -> Optional[str]:

    text = normalize(message)

    for key, value in PURPOSES.items():

        if re.search(
            rf"\b{re.escape(key)}\b",
            text,
        ):
            return value

    return None


# =========================================================
# PROPERTY TYPE EXTRACTION
# =========================================================

def extract_property_type(
    message: str,
) -> Optional[str]:

    text = normalize(message)

    for key in sorted(
        PROPERTY_TYPES,
        key=len,
        reverse=True,
    ):

        if re.search(
            rf"\b{re.escape(key)}\b",
            text,
        ):
            return PROPERTY_TYPES[key]

    return None


# =========================================================
# LOCATION EXTRACTION
# =========================================================

def extract_location(
    message: str,
) -> Optional[str]:

    text = clean_text(message)
    lower = text.lower()

    # -----------------------------------------------------
    # Specific locations first
    # -----------------------------------------------------

    for location in sorted(
        NIGERIAN_LOCATIONS,
        key=len,
        reverse=True,
    ):

        if re.search(
            rf"\b{re.escape(location)}\b",
            lower,
        ):

            aliases = {
                "ph": "Port Harcourt",
                "vi": "Victoria Island",
                "benin": "Benin City",
                "oshogbo": "Osogbo",
            }

            return aliases.get(
                location,
                location.title(),
            )

    # -----------------------------------------------------
    # States
    # -----------------------------------------------------

    for state in sorted(
        NIGERIAN_STATES,
        key=len,
        reverse=True,
    ):

        if re.search(
            rf"\b{re.escape(state)}\b",
            lower,
        ):

            if state in {
                "fct",
                "abuja",
            }:
                return "Abuja"

            return state.title()

    # -----------------------------------------------------
    # Natural phrases
    # -----------------------------------------------------

    patterns = [
        r"\bin\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)",
        r"\bat\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)",
        r"\baround\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)",
        r"\bnear\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)",
        r"\blocation\s+is\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)",
        r"\blocation:\s*([A-Za-zÀ-ÖØ-öø-ÿ'’\- ]+)",
    ]

    stop_words = {
        "and",
        "with",
        "for",
        "i",
        "my",
        "the",
        "a",
        "an",
        "within",
        "budget",
        "looking",
        "want",
        "need",
    }

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        candidate = clean_text(
            match.group(1)
        )

        words = candidate.split()
        filtered = []

        for word in words:

            if word.lower() in stop_words:
                break

            if re.search(
                r"\d",
                word,
            ):
                break

            filtered.append(word)

        if filtered:

            location = " ".join(
                filtered
            ).strip()

            if location:
                return location.title()

    return None


# =========================================================
# BUDGET EXTRACTION
# =========================================================

def extract_budget(message: str):

    # IMPORTANT:
    # Phone numbers are removed before budget detection.

    text = remove_phone_numbers(
        normalize(message)
    )

    # -----------------------------------------------------
    # 50 million
    # ₦50 million
    # 50 million naira
    # -----------------------------------------------------

    million_match = re.search(
        r"(?:₦|ngn|n)?\s*"
        r"(\d+(?:\.\d+)?)"
        r"\s*m(?:illion)?\b",
        text,
        re.IGNORECASE,
    )

    if not million_match:

        million_match = re.search(
            r"(?:₦|ngn|n)?\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*million\b",
            text,
            re.IGNORECASE,
        )

    if million_match:

        value = (
            float(
                million_match.group(1)
            )
            * 1_000_000
        )

        return (
            value,
            f"₦{value:,.0f}",
        )

    # -----------------------------------------------------
    # 50k / 500k / 2.5m
    # -----------------------------------------------------

    shorthand = re.search(
        r"(?:₦|ngn|n)?\s*"
        r"(\d+(?:\.\d+)?)"
        r"\s*(k|m|b)\b",
        text,
        re.IGNORECASE,
    )

    if shorthand:

        number = float(
            shorthand.group(1)
        )

        unit = shorthand.group(2).lower()

        multiplier = {
            "k": 1_000,
            "m": 1_000_000,
            "b": 1_000_000_000,
        }[unit]

        value = number * multiplier

        return (
            value,
            f"₦{value:,.0f}",
        )

    # -----------------------------------------------------
    # Explicit currency
    # ₦50,000,000
    # N50,000,000
    # NGN 50,000,000
    # -----------------------------------------------------

    currency_match = re.search(
        r"(?:₦|ngn|n)\s*"
        r"([\d,]+(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )

    if currency_match:

        raw = (
            currency_match.group(1)
            .replace(",", "")
        )

        try:

            value = float(raw)

            if value >= 100_000:

                return (
                    value,
                    f"₦{value:,.0f}",
                )

        except ValueError:
            pass

    # -----------------------------------------------------
    # Plain large numbers
    #
    # Only numbers >= 100,000 are considered.
    # This prevents bedroom counts, dates, etc.
    # from becoming budgets.
    # -----------------------------------------------------

    numbers = re.findall(
        r"\b\d{5,12}\b",
        text,
    )

    for number in numbers:

        try:

            value = float(number)

            if value >= 100_000:

                return (
                    value,
                    f"₦{value:,.0f}",
                )

        except ValueError:
            continue

    return None, None


# =========================================================
# BEDROOM EXTRACTION
# =========================================================

def extract_bedrooms(
    message: str,
) -> Optional[int]:

    text = normalize(message)

    patterns = [
        r"(\d+)\s*bedrooms?",
        r"(\d+)\s*bed(?:room)?",
        r"(\d+)\s*br\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:
            return int(
                match.group(1)
            )

    return None


# =========================================================
# TIMELINE EXTRACTION
# =========================================================

def extract_timeline(
    message: str,
) -> Optional[str]:

    text = normalize(message)

    patterns = [
        r"(?:within|in|by)\s+"
        r"(\d+)\s*"
        r"(day|days|week|weeks|month|months|year|years)",

        r"\b(immediately|"
        r"as soon as possible|"
        r"asap|"
        r"now)\b",

        r"\b(next month|"
        r"next week|"
        r"this month|"
        r"this week)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            return match.group(0)

    return None


# =========================================================
# PROPERTY IMAGE URL EXTRACTION
# =========================================================

def extract_image_urls(message: str):

    urls = re.findall(
        r"https?://[^\s]+",
        message,
        re.IGNORECASE,
    )

    image_urls = []

    for url in urls:

        clean_url = url.rstrip(
            ".,!?);]"
        )

        if re.search(
            r"\.(jpg|jpeg|png|webp|gif)"
            r"(\?.*)?$",
            clean_url,
            re.IGNORECASE,
        ):

            if clean_url not in image_urls:
                image_urls.append(
                    clean_url
                )

    return image_urls


# =========================================================
# LEAD QUALITY
# =========================================================

def calculate_lead_quality(
    lead,
):

    required = [
        lead.get("location"),
        lead.get("property_type"),
        lead.get("purpose"),
        lead.get("budget"),
        lead.get("timeline"),
    ]

    count = sum(
        1
        for value in required
        if value
    )

    if count == 5:
        return "HOT"

    if count >= 3:
        return "WARM"

    return "COLD"


# =========================================================
# NEXT MISSING FIELD
# =========================================================

def next_missing_field(
    lead,
):

    required = [
        (
            "purpose",
            "Are you looking to buy, rent, or invest?",
        ),
        (
            "location",
            "Which city or area are you interested in?",
        ),
        (
            "property_type",
            "What type of property are you looking for?",
        ),
        (
            "budget",
            "What is your approximate budget?",
        ),
        (
            "timeline",
            "When are you looking to move or complete the purchase?",
        ),
        (
            "name",
            "May I have your name?",
        ),
        (
            "phone",
            "What phone number can we use to contact you?",
        ),
        (
            "email",
            "What is your email address?",
        ),
    ]

    for field, _ in required:

        if not lead.get(field):
            return field

    return None


# =========================================================
# UPDATE LEAD
# =========================================================

def update_lead(
    lead,
    message,
):

    name = extract_name(
        message
    )

    email = extract_email(
        message
    )

    phone = extract_phone(
        message
    )

    location = extract_location(
        message
    )

    property_type = extract_property_type(
        message
    )

    purpose = extract_purpose(
        message
    )

    budget, budget_text = extract_budget(
        message
    )

    bedrooms = extract_bedrooms(
        message
    )

    timeline = extract_timeline(
        message
    )

    images = extract_image_urls(
        message
    )

    if name:
        lead["name"] = name

    if email:
        lead["email"] = email

    if phone:
        lead["phone"] = phone

    if location:
        lead["location"] = location

    if property_type:
        lead["property_type"] = property_type

    if purpose:
        lead["purpose"] = purpose

    if budget is not None:
        lead["budget"] = budget
        lead["budget_text"] = budget_text

    if bedrooms is not None:
        lead["bedrooms"] = bedrooms

    if timeline:
        lead["timeline"] = timeline

    if images:

        for image in images:

            if image not in lead[
                "property_images"
            ]:

                lead[
                    "property_images"
                ].append(image)

    # -----------------------------------------------------
    # Store useful conversation text
    #
    # Avoid putting pure contact information into the
    # main message unnecessarily.
    # -----------------------------------------------------

    message_for_storage = message.strip()

    if message_for_storage:

        if not re.fullmatch(
            r"(?:my\s+)?"
            r"(?:email|e-mail)\s*(?:is|:)?\s*"
            r"\S+@\S+\.\S+",
            message_for_storage,
            re.IGNORECASE,
        ) and not re.fullmatch(
            r"(?:my\s+)?"
            r"phone\s*(?:number)?\s*(?:is|:)?\s*"
            r"[\d+\s().-]+",
            message_for_storage,
            re.IGNORECASE,
        ):

            if lead["message"]:

                lead["message"] += (
                    " | "
                    + message_for_storage
                )

            else:

                lead["message"] = (
                    message_for_storage
                )

    lead["lead_quality"] = (
        calculate_lead_quality(
            lead
        )
    )

    return lead


# =========================================================
# CHAT RESPONSE
# =========================================================

def generate_reply(
    lead,
):

    missing = next_missing_field(
        lead
    )

    if missing == "purpose":
        return (
            "Are you looking to buy, "
            "rent, or invest?"
        )

    if missing == "location":
        return (
            "Which city or area are "
            "you interested in?"
        )

    if missing == "property_type":
        return (
            "What type of property "
            "are you looking for?"
        )

    if missing == "budget":
        return (
            "What is your approximate budget?"
        )

    if missing == "timeline":
        return (
            "When are you looking to move "
            "or complete the purchase?"
        )

    if missing == "name":
        return "May I have your name?"

    if missing == "phone":
        return (
            "What phone number can we use "
            "to contact you?"
        )

    if missing == "email":
        return (
            "What is your email address?"
        )

    return (
        "Thank you. I have everything I need. "
        "A property specialist can now "
        "follow up with you."
    )


# =========================================================
# SEND LEAD TO N8N
# =========================================================

def send_to_n8n(
    lead,
):

    if not N8N_WEBHOOK_URL:
        return False

    payload = {
        "name": lead.get("name"),
        "email": lead.get("email"),
        "phone": lead.get("phone"),
        "location": lead.get("location"),
        "property_type": lead.get("property_type"),
        "purpose": lead.get("purpose"),
        "budget": lead.get("budget"),
        "bedrooms": lead.get("bedrooms"),
        "timeline": lead.get("timeline"),
        "message": lead.get("message"),
        "lead_quality": lead.get("lead_quality"),
        "main_problem": lead.get("main_problem"),
        "recommended_action": lead.get(
            "recommended_action"
        ),
        "property_images": lead.get(
            "property_images",
            [],
        ),
        "source": "real-estate-webhook",
    }

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=15,
        )

        print(
            "n8n status:",
            response.status_code,
        )

        return (
            200
            <= response.status_code
            < 300
        )

    except Exception as exc:

        print(
            "n8n error:",
            exc,
        )

        return False


# =========================================================
# SAVE LEAD TO SUPABASE
# =========================================================

def save_to_supabase(
    lead,
):

    if not SUPABASE_URL:
        return False

    if not SUPABASE_KEY:
        return False

    table_name = "Real estate lead"

    url = (
        SUPABASE_URL.rstrip("/")
        + "/rest/v1/"
        + table_name.replace(
            " ",
            "%20",
        )
    )

    payload = {
        "name": lead.get("name"),
        "email": lead.get("email"),
        "phone": lead.get("phone"),
        "location": lead.get("location"),
        "property_type": lead.get(
            "property_type"
        ),
        "purpose": lead.get(
            "purpose"
        ),
        "budget": lead.get(
            "budget"
        ),

        # Keep this aligned with the
        # current chatbot payload.
        "bedrooms": lead.get(
            "bedrooms"
        ),

        "timeline": lead.get(
            "timeline"
        ),
        "message": lead.get(
            "message"
        ),
        "lead_quality": lead.get(
            "lead_quality"
        ),
        "main_problem": lead.get(
            "main_problem"
        ),
        "recommended_action": lead.get(
            "recommended_action"
        ),
        "source": "real-estate-chatbot",
        "created_at": lead.get(
            "created_at"
        ),
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": (
            f"Bearer {SUPABASE_KEY}"
        ),
        "Content-Type": (
            "application/json"
        ),
        "Prefer": "return=minimal",
    }

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15,
        )

        print(
            "Supabase status:",
            response.status_code,
        )

        if not (
            200
            <= response.status_code
            < 300
        ):

            print(
                "Supabase response:",
                response.text,
            )

        return (
            200
            <= response.status_code
            < 300
        )

    except Exception as exc:

        print(
            "Supabase error:",
            exc,
        )

        return False


# =========================================================
# CREATE NEW SESSION
# =========================================================

def create_session(
    session_id: str,
):

    return {
        "session_id": session_id,
        "name": None,
        "email": None,
        "phone": None,
        "location": None,
        "property_type": None,
        "purpose": None,
        "budget": None,
        "budget_text": None,
        "bedrooms": None,
        "timeline": None,
        "message": "",
        "lead_quality": "COLD",
        "main_problem": None,
        "recommended_action": None,
        "source": "real-estate-chatbot",
        "property_images": [],
        "n8n_sent": False,
        "supabase_saved": False,
        "created_at": (
            datetime.utcnow().isoformat()
        ),
    }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "success": True,
        "message": (
            "PropertyPilot AI API is running"
        ),
        "version": "2.0.0",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/api/v1/health")
def health():

    return {
        "status": "healthy",
        "message": (
            "PropertyPilot AI API is running"
        ),
    }


# =========================================================
# CHAT
# =========================================================

@app.post("/api/v1/chat")
def chat(
    request: ChatRequest,
):

    session_id = clean_text(
        request.session_id
    )

    if not session_id:

        session_id = (
            datetime.utcnow()
            .strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

    if session_id not in sessions:

        sessions[session_id] = (
            create_session(
                session_id
            )
        )

    lead = sessions[
        session_id
    ]

    update_lead(
        lead,
        request.message,
    )

    missing = next_missing_field(
        lead
    )

    complete = missing is None

    # -----------------------------------------------------
    # Send complete leads once
    # -----------------------------------------------------

    if complete:

        if not lead["n8n_sent"]:

            lead["n8n_sent"] = (
                send_to_n8n(
                    lead
                )
            )

        if not lead[
            "supabase_saved"
        ]:

            lead[
                "supabase_saved"
            ] = save_to_supabase(
                lead
            )

    reply = generate_reply(
        lead
    )

    return {
        "success": True,
        "session_id": session_id,
        "reply": reply,
        "lead_quality": lead[
            "lead_quality"
        ],
        "missing_field": missing,
        "complete": complete,
        "lead": lead,
        "integrations": {
            "n8n": {
                "sent": lead[
                    "n8n_sent"
                ]
            },
            "supabase": {
                "saved": lead[
                    "supabase_saved"
                ]
            },
        },
    }


# =========================================================
# GET SESSION
# =========================================================

@app.get(
    "/api/v1/sessions/{session_id}"
)
def get_session(
    session_id: str,
):

    lead = sessions.get(
        session_id
    )

    if not lead:

        return {
            "success": False,
            "message": (
                "Session not found"
            ),
        }

    return {
        "success": True,
        "lead": lead,
    }


# =========================================================
# DELETE SESSION
# =========================================================

@app.delete(
    "/api/v1/sessions/{session_id}"
)
def delete_session(
    session_id: str,
):

    if session_id in sessions:

        del sessions[
            session_id
        ]

        return {
            "success": True,
            "message": (
                "Session deleted"
            ),
        }

    return {
        "success": False,
        "message": (
            "Session not found"
        ),
    }


# =========================================================
# MANUAL LEAD ENDPOINT
# =========================================================

@app.post("/api/v1/leads")
def create_lead(
    request: LeadRequest,
):

    lead = request.model_dump()

    lead[
        "created_at"
    ] = datetime.utcnow().isoformat()

    if not lead.get(
        "lead_quality"
    ):

        lead[
            "lead_quality"
        ] = calculate_lead_quality(
            lead
        )

    if not lead.get(
        "property_images"
    ):

        lead[
            "property_images"
        ] = []

    n8n_sent = send_to_n8n(
        lead
    )

    supabase_saved = (
        save_to_supabase(
            lead
        )
    )

    return {
        "success": True,
        "message": "Lead received",
        "lead": lead,
        "integrations": {
            "n8n": {
                "sent": n8n_sent
            },
            "supabase": {
                "saved": supabase_saved
            },
        },
    }