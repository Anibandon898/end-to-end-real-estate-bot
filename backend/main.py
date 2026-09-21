import os
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.extractors import (
    clean,
    create_session,
    update_lead,
    next_missing_field,
    calculate_lead_quality,
    QUESTIONS,
)


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

load_dotenv(
    os.path.join(
        PROJECT_ROOT,
        ".env"
    )
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="PropertyPilot AI",
    description="Smart Real Estate Assistant API",
    version="2.5.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/real-estate"
)

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    ""
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    ""
)


# ============================================================
# SUPABASE CONFIGURATION
# ============================================================

SUPABASE_TABLE = "Real estate lead"
SUPABASE_BUCKET = "property-images"


# ============================================================
# IMAGE CONFIGURATION
# ============================================================

MAX_IMAGE_SIZE = 20 * 1024 * 1024
MAX_IMAGES = 10


# ============================================================
# IN-MEMORY SESSION STORAGE
# ============================================================

sessions: Dict[str, Dict[str, Any]] = {}

uploaded_images: Dict[str, List[str]] = {}


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


class LeadRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
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
    source: Optional[str] = "real-estate-chatbot"


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "PropertyPilot AI backend is running",
        "version": "2.5.0"
    }


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "message": "PropertyPilot AI API is running"
    }


# ============================================================
# CREATE NEW SESSION
# ============================================================

@app.post("/api/v1/new-session")
def new_session():

    session_id = (
        "propertypilot-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    session = create_session()

    session["session_id"] = session_id

    sessions[session_id] = session

    uploaded_images[session_id] = []

    return {
        "success": True,
        "session_id": session_id,
        "message": "New PropertyPilot conversation started."
    }


# ============================================================
# QUESTION HELPER
# ============================================================

def get_question(field: str) -> str:

    for question_field, question_text in QUESTIONS:

        if question_field == field:
            return question_text

    return (
        "Could you provide more information "
        "about your property needs?"
    )


# ============================================================
# BUDGET FORMATTER
# ============================================================

def format_budget(
    budget: Any
) -> Optional[str]:

    if budget is None:
        return None

    try:
        amount = float(budget)
    except (TypeError, ValueError):
        return None

    return f"₦{amount:,.0f}"


# ============================================================
# BUILD PROPERTY REQUEST SUMMARY
# ============================================================

def build_lead_summary(
    session: Dict[str, Any]
) -> str:

    parts: List[str] = []

    purpose = session.get("purpose")
    property_type = session.get("property_type")
    location = session.get("location")
    budget = session.get("budget")
    bedrooms = session.get("bedrooms")
    timeline = session.get("timeline")

    # Purpose
    if purpose:
        parts.append(str(purpose))

    # Property type
    if property_type:
        parts.append(str(property_type))

    # Location
    if location:
        parts.append(
            f"in {location}"
        )

    # Bedrooms
    if bedrooms is not None:

        bedroom_word = (
            "bedroom"
            if bedrooms == 1
            else "bedrooms"
        )

        parts.append(
            f"with {bedrooms} {bedroom_word}"
        )

    # Budget
    budget_text = format_budget(budget)

    if budget_text:

        parts.append(
            f"with a budget of {budget_text}"
        )

    # Timeline
    if timeline:

        timeline_text = str(
            timeline
        ).strip()

        # Prevent:
        # "within within 1 month"
        if timeline_text.lower().startswith(
            "within "
        ):
            timeline_text = timeline_text[
                len("within "):
            ].strip()

        if timeline_text:

            parts.append(
                f"within {timeline_text}"
            )

    # No information yet
    if not parts:

        return (
            "Customer is interested in "
            "a real estate property."
        )

    summary = " ".join(parts)

    summary = re.sub(
        r"\s+",
        " ",
        summary
    ).strip()

    return (
        f"Customer is looking for {summary}."
    )


# ============================================================
# CHECK FOR CONTACT-ONLY MESSAGE
# ============================================================

def is_contact_only_message(
    message: str
) -> bool:

    text = clean(message)

    if not text:
        return True

    # Email
    email_pattern = (
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"
    )

    if re.fullmatch(
        email_pattern,
        text
    ):
        return True

    # Phone
    phone_digits = re.sub(
        r"\D",
        "",
        text
    )

    if (
        10 <= len(phone_digits) <= 15
        and (
            text.startswith("+")
            or text.replace(
                " ",
                ""
            ).replace(
                "-",
                ""
            ).isdigit()
        )
    ):
        return True

    return False


# ============================================================
# UPDATE LEAD MESSAGE
# ============================================================

def update_lead_message(
    session: Dict[str, Any]
) -> None:

    summary = build_lead_summary(
        session
    )

    session["message"] = summary

    session["main_problem"] = summary


# ============================================================
# IMAGE UPLOAD
# ============================================================

def upload_one_image(
    file: UploadFile,
    session_id: str
) -> str:

    if not SUPABASE_URL or not SUPABASE_KEY:

        raise HTTPException(
            status_code=500,
            detail=(
                "Supabase configuration is missing."
            )
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image type. "
                "Please upload JPG, PNG, or WEBP."
            )
        )

    contents = file.file.read()

    if len(contents) > MAX_IMAGE_SIZE:

        raise HTTPException(
            status_code=413,
            detail=(
                "Image is too large. "
                "Maximum size is 20MB."
            )
        )

    original_name = (
        file.filename
        or "property-image.jpg"
    )

    extension = os.path.splitext(
        original_name
    )[1].lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }:

        extension = ".jpg"

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )

    safe_session_id = clean(
        session_id
    ).replace(
        " ",
        "-"
    )

    file_name = (
        f"{safe_session_id}/"
        f"{timestamp}"
        f"{extension}"
    )

    storage_url = (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/storage/v1/object/"
        f"{SUPABASE_BUCKET}/"
        f"{file_name}"
    )

    headers = {
        "Authorization": (
            f"Bearer {SUPABASE_KEY}"
        ),
        "apikey": SUPABASE_KEY,
        "Content-Type": file.content_type,
        "x-upsert": "true"
    }

    try:

        response = requests.post(
            storage_url,
            headers=headers,
            data=contents,
            timeout=60
        )

    except Exception as exc:

        print(
            "IMAGE UPLOAD ERROR:",
            str(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not connect to "
                "Supabase Storage."
            )
        )

    if response.status_code not in (
        200,
        201
    ):

        print(
            "IMAGE UPLOAD FAILED:",
            response.status_code,
            response.text
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not upload property "
                "image to Supabase Storage."
            )
        )

    public_url = (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/storage/v1/object/public/"
        f"{SUPABASE_BUCKET}/"
        f"{file_name}"
    )

    if session_id not in uploaded_images:

        uploaded_images[session_id] = []

    if len(
        uploaded_images[session_id]
    ) < MAX_IMAGES:

        uploaded_images[
            session_id
        ].append(
            public_url
        )

    print(
        "PROPERTY IMAGE UPLOADED:",
        public_url
    )

    return public_url


# ============================================================
# IMAGE UPLOAD ENDPOINT
# ============================================================

@app.post("/api/v1/upload-image")
async def upload_image(
    session_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None)
):

    if not session_id.strip():

        raise HTTPException(
            status_code=400,
            detail="session_id is required."
        )

    uploaded_urls: List[str] = []

    # Single image
    if file is not None:

        if len(uploaded_urls) < MAX_IMAGES:

            uploaded_urls.append(
                upload_one_image(
                    file,
                    session_id
                )
            )

    # Multiple images
    if files:

        for current_file in files:

            if (
                len(uploaded_urls)
                >= MAX_IMAGES
            ):
                break

            uploaded_urls.append(
                upload_one_image(
                    current_file,
                    session_id
                )
            )

    if not uploaded_urls:

        raise HTTPException(
            status_code=400,
            detail=(
                "No image file was provided."
            )
        )

    return {
        "success": True,
        "session_id": session_id,
        "urls": uploaded_urls,
        "url": uploaded_urls[0],
        "image_url": uploaded_urls[0],
        "property_images": uploaded_urls,
        "count": len(uploaded_urls)
    }


# ============================================================
# SEND LEAD TO N8N
# ============================================================

def send_to_n8n(
    session: Dict[str, Any]
) -> Dict[str, Any]:

    property_images = uploaded_images.get(
        session.get("session_id", ""),
        []
    )

    update_lead_message(
        session
    )

    payload = {
        "name": session.get("name"),
        "email": session.get("email"),
        "phone": session.get("phone"),
        "location": session.get("location"),
        "property_type": session.get(
            "property_type"
        ),
        "purpose": session.get("purpose"),
        "budget": session.get("budget"),
        "bedrooms": session.get("bedrooms"),
        "timeline": session.get("timeline"),
        "message": session.get("message"),
        "lead_quality": session.get(
            "lead_quality"
        ),
        "main_problem": session.get(
            "main_problem"
        ),
        "recommended_action": (
            "Contact immediately"
            if session.get(
                "lead_quality"
            ) == "HOT"
            else "Follow up with property "
                 "recommendations"
        ),
        "property_images": property_images,
        "source": "real-estate-webhook"
    }

    print(
        "\n========== N8N PAYLOAD =========="
    )

    print(payload)

    print(
        "=================================\n"
    )

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=30
        )

        print(
            "N8N STATUS:",
            response.status_code
        )

        print(
            "N8N RESPONSE:",
            response.text
        )

        success = (
            200
            <= response.status_code
            < 300
        )

        if success:

            session["n8n_sent"] = True

        return {
            "sent": success,
            "status_code": response.status_code,
            "response": response.text
        }

    except Exception as exc:

        print(
            "N8N ERROR:",
            str(exc)
        )

        return {
            "sent": False,
            "status_code": None,
            "response": str(exc)
        }


# ============================================================
# SAVE LEAD TO SUPABASE
# ============================================================

def save_to_supabase(
    session: Dict[str, Any]
) -> Dict[str, Any]:

    if not SUPABASE_URL or not SUPABASE_KEY:

        return {
            "saved": False,
            "status_code": None,
            "response": (
                "Supabase configuration "
                "is missing."
            )
        }

    update_lead_message(
        session
    )

    property_images = uploaded_images.get(
        session.get("session_id", ""),
        []
    )

    payload = {
        "name": session.get("name"),
        "email": session.get("email"),
        "phone": session.get("phone"),
        "location": session.get("location"),
        "property_type": session.get(
            "property_type"
        ),
        "purpose": session.get("purpose"),
        "budget": session.get("budget"),
        "bedrooms": session.get("bedrooms"),
        "timeline": session.get("timeline"),
        "message": session.get("message"),
        "lead_quality": session.get(
            "lead_quality"
        ),
        "main_problem": session.get(
            "main_problem"
        ),
        "recommended_action": (
            "Contact immediately"
            if session.get(
                "lead_quality"
            ) == "HOT"
            else "Follow up with property "
                 "recommendations"
        ),
        "property_images": property_images,
        "source": "real-estate-chatbot"
    }

    print(
        "\n========== SUPABASE PAYLOAD =========="
    )

    print(payload)

    print(
        "======================================\n"
    )

    table_name = requests.utils.quote(
        SUPABASE_TABLE,
        safe=""
    )

    url = (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table_name}"
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": (
            f"Bearer {SUPABASE_KEY}"
        ),
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(
            "SUPABASE STATUS:",
            response.status_code
        )

        print(
            "SUPABASE RESPONSE:",
            response.text
        )

        success = (
            200
            <= response.status_code
            < 300
        )

        if success:

            session[
                "supabase_saved"
            ] = True

        return {
            "saved": success,
            "status_code": response.status_code,
            "response": response.text
        }

    except Exception as exc:

        print(
            "SUPABASE ERROR:",
            str(exc)
        )

        return {
            "saved": False,
            "status_code": None,
            "response": str(exc)
        }


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/api/v1/chat")
def chat(
    request: ChatRequest
):

    session_id = clean(
        request.session_id
    )

    message = clean(
        request.message
    )

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "session_id is required."
            )
        )

    if not message:

        raise HTTPException(
            status_code=400,
            detail="message is required."
        )

    # Create session if necessary
    if session_id not in sessions:

        session = create_session()

        session["session_id"] = session_id

        sessions[session_id] = session

    session = sessions[session_id]

    # Extract information from the user's message
    update_lead(
        session,
        message
    )

    # Calculate lead quality
    session["lead_quality"] = (
        calculate_lead_quality(
            session
        )
    )

    # Build property summary.
    #
    # IMPORTANT:
    # We do NOT save the final phone/email
    # message as the property request.
    update_lead_message(
        session
    )

    # Find next missing field
    missing_field = next_missing_field(
        session
    )

    # ========================================================
    # LEAD COMPLETE
    # ========================================================

    if missing_field is None:

        n8n_result = {
            "sent": session.get(
                "n8n_sent",
                False
            )
        }

        supabase_result = {
            "saved": session.get(
                "supabase_saved",
                False
            )
        }

        # Send to n8n once
        if not session.get(
            "n8n_sent",
            False
        ):

            n8n_result = send_to_n8n(
                session
            )

        # Save to Supabase once
        if not session.get(
            "supabase_saved",
            False
        ):

            supabase_result = (
                save_to_supabase(
                    session
                )
            )

        session["lead_complete"] = True

        return {
            "success": True,
            "session_id": session_id,
            "reply": (
                "Thank you. I have all "
                "the details I need. "
                "Our team will review "
                "your request and get "
                "back to you shortly."
            ),
            "missing_field": None,
            "lead_complete": True,
            "lead_quality": session.get(
                "lead_quality"
            ),
            "lead": {
                "name": session.get(
                    "name"
                ),
                "email": session.get(
                    "email"
                ),
                "phone": session.get(
                    "phone"
                ),
                "location": session.get(
                    "location"
                ),
                "property_type": session.get(
                    "property_type"
                ),
                "purpose": session.get(
                    "purpose"
                ),
                "budget": session.get(
                    "budget"
                ),
                "bedrooms": session.get(
                    "bedrooms"
                ),
                "timeline": session.get(
                    "timeline"
                ),
                "message": session.get(
                    "message"
                ),
                "main_problem": session.get(
                    "main_problem"
                ),
                "lead_quality": session.get(
                    "lead_quality"
                ),
                "property_images": (
                    uploaded_images.get(
                        session_id,
                        []
                    )
                )
            },
            "integrations": {
                "n8n": n8n_result,
                "supabase": supabase_result
            }
        }

    # ========================================================
    # ASK NEXT QUESTION
    # ========================================================

    reply = get_question(
        missing_field
    )

    return {
        "success": True,
        "session_id": session_id,
        "reply": reply,
        "missing_field": missing_field,
        "lead_complete": False,
        "lead_quality": session.get(
            "lead_quality",
            "COLD"
        ),
        "integrations": {
            "n8n": {
                "sent": session.get(
                    "n8n_sent",
                    False
                )
            },
            "supabase": {
                "saved": session.get(
                    "supabase_saved",
                    False
                )
            }
        },
        "lead": {
            "name": session.get(
                "name"
            ),
            "email": session.get(
                "email"
            ),
            "phone": session.get(
                "phone"
            ),
            "location": session.get(
                "location"
            ),
            "property_type": session.get(
                "property_type"
            ),
            "purpose": session.get(
                "purpose"
            ),
            "budget": session.get(
                "budget"
            ),
            "bedrooms": session.get(
                "bedrooms"
            ),
            "timeline": session.get(
                "timeline"
            ),
            "message": session.get(
                "message"
            ),
            "property_images": (
                uploaded_images.get(
                    session_id,
                    []
                )
            )
        }
    }


# ============================================================
# DIRECT LEAD ENDPOINT
# ============================================================

@app.post("/api/v1/leads")
def create_lead(
    lead: LeadRequest
):

    session = create_session()

    session["session_id"] = (
        "direct-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    session["name"] = lead.name

    session["email"] = lead.email

    session["phone"] = lead.phone

    session["location"] = lead.location

    session["property_type"] = (
        lead.property_type
    )

    session["purpose"] = lead.purpose

    session["budget"] = lead.budget

    session["bedrooms"] = lead.bedrooms

    session["timeline"] = lead.timeline

    session["lead_quality"] = (
        lead.lead_quality
        or calculate_lead_quality(
            session
        )
    )

    update_lead_message(
        session
    )

    n8n_result = send_to_n8n(
        session
    )

    supabase_result = (
        save_to_supabase(
            session
        )
    )

    return {
        "success": True,
        "message": (
            "Lead received and processed."
        ),
        "lead": {
            "name": session.get(
                "name"
            ),
            "email": session.get(
                "email"
            ),
            "phone": session.get(
                "phone"
            ),
            "location": session.get(
                "location"
            ),
            "property_type": session.get(
                "property_type"
            ),
            "purpose": session.get(
                "purpose"
            ),
            "budget": session.get(
                "budget"
            ),
            "bedrooms": session.get(
                "bedrooms"
            ),
            "timeline": session.get(
                "timeline"
            ),
            "message": session.get(
                "message"
            ),
            "main_problem": session.get(
                "main_problem"
            ),
            "lead_quality": session.get(
                "lead_quality"
            ),
            "property_images": (
                uploaded_images.get(
                    session.get(
                        "session_id"
                    ),
                    []
                )
            )
        },
        "n8n": n8n_result,
        "supabase": supabase_result
    }


# ============================================================
# STARTUP MESSAGE
# ============================================================

@app.on_event("startup")
def startup_event():

    print(
        "\n"
        "==============================================\n"
        "       PROPERTY PILOT AI BACKEND\n"
        "==============================================\n"
        "FastAPI: RUNNING\n"
        f"n8n: {N8N_WEBHOOK_URL}\n"
        f"Supabase: "
        f"{'CONFIGURED' if SUPABASE_URL and SUPABASE_KEY else 'NOT CONFIGURED'}\n"
        f"Storage bucket: {SUPABASE_BUCKET}\n"
        "Maximum image size: 20MB\n"
        "Maximum images: 10\n"
        "==============================================\n"
    )