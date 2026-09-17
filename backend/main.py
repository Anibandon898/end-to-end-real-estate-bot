import os
import uuid
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


# =========================================================
# ENVIRONMENT
# =========================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(
    os.path.join(PROJECT_ROOT, ".env")
)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="PropertyPilot AI",
    version="2.4.0"
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

SUPABASE_TABLE = "Real estate lead"

SUPABASE_STORAGE_BUCKET = os.getenv(
    "SUPABASE_STORAGE_BUCKET",
    "property-images"
)

MAX_IMAGE_SIZE = 10 * 1024 * 1024

MAX_IMAGES = 10

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


# =========================================================
# SESSION STORAGE
# =========================================================

sessions: Dict[str, Dict[str, Any]] = {}


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
    state: str = ""
    property_type: str = ""
    purpose: str = ""
    budget: Optional[float] = None
    budget_text: str = ""
    bedrooms: Optional[int] = None
    timeline: str = ""
    message: str = ""
    lead_quality: str = ""
    main_problem: str = ""
    recommended_action: str = ""
    source: str = "real-estate-chatbot"


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "PropertyPilot AI is running"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "message": "PropertyPilot AI API is running"
    }


# =========================================================
# SUPABASE IMAGE UPLOAD
# =========================================================

def upload_image_to_supabase(
    file: UploadFile,
    file_bytes: bytes,
    session_id: str
) -> str:

    if not SUPABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL is missing"
        )

    if not SUPABASE_KEY:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_KEY is missing"
        )

    extension_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }

    extension = extension_map.get(
        file.content_type,
        ""
    )

    if not extension:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type"
        )

    filename = (
        uuid.uuid4().hex
        + extension
    )

    # The bucket is already "property-images".
    # Therefore we only need the folder/file path here.
    storage_path = (
        session_id
        + "/"
        + filename
    )

    upload_url = (
        SUPABASE_URL.rstrip("/")
        + "/storage/v1/object/"
        + SUPABASE_STORAGE_BUCKET
        + "/"
        + storage_path
    )

    headers = {
        "Authorization": "Bearer " + SUPABASE_KEY,
        "apikey": SUPABASE_KEY,
        "Content-Type": file.content_type,
        "x-upsert": "false"
    }

    print("")
    print("========== SUPABASE IMAGE UPLOAD ==========")
    print("Bucket:", SUPABASE_STORAGE_BUCKET)
    print("Path:", storage_path)
    print("Filename:", file.filename)
    print("Type:", file.content_type)
    print("Size:", len(file_bytes))

    try:
        response = requests.post(
            upload_url,
            headers=headers,
            data=file_bytes,
            timeout=60
        )

    except Exception as error:
        print(
            "Supabase Storage connection error:",
            repr(error)
        )

        raise HTTPException(
            status_code=502,
            detail="Could not connect to Supabase Storage"
        )

    print(
        "Storage status:",
        response.status_code
    )

    print(
        "Storage response:",
        response.text
    )

    print("============================================")
    print("")

    if not (
        200 <= response.status_code < 300
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Supabase Storage upload failed: "
                + response.text
            )
        )

    public_url = (
        SUPABASE_URL.rstrip("/")
        + "/storage/v1/object/public/"
        + SUPABASE_STORAGE_BUCKET
        + "/"
        + storage_path
    )

    return public_url


# =========================================================
# PROPERTY IMAGE ENDPOINT
# =========================================================

@app.post("/api/v1/upload")
async def upload_property_images(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...)
):

    session_id = clean(session_id)

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required"
        )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one image is required"
        )

    if len(files) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=(
                "You can upload a maximum of "
                + str(MAX_IMAGES)
                + " images at once."
            )
        )

    if session_id not in sessions:
        sessions[session_id] = create_session(
            session_id
        )

    session = sessions[session_id]

    if "property_images" not in session:
        session["property_images"] = []

    uploaded_images = []

    for file in files:

        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=(
                    str(file.filename)
                    + " is not a supported image type. "
                    + "Use JPG, PNG, or WebP."
                )
            )

        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    str(file.filename)
                    + " is empty."
                )
            )

        if len(file_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=(
                    str(file.filename)
                    + " is too large. "
                    + "Maximum size is 10 MB per image."
                )
            )

        public_url = upload_image_to_supabase(
            file=file,
            file_bytes=file_bytes,
            session_id=session_id
        )

        image_record = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_bytes),
            "url": public_url
        }

        uploaded_images.append(
            image_record
        )

        session["property_images"].append(
            image_record
        )

    return {
        "success": True,
        "session_id": session_id,
        "message": (
            str(len(uploaded_images))
            + " property image(s) uploaded successfully."
        ),
        "images": uploaded_images,
        "property_images": session.get(
            "property_images",
            []
        )
    }


# =========================================================
# SEND LEAD TO N8N
# =========================================================

def send_to_n8n(
    session: Dict[str, Any]
) -> bool:

    if session.get("n8n_sent"):
        return True

    payload = {
        "name": session.get("name", ""),
        "email": session.get("email", ""),
        "phone": session.get("phone", ""),
        "location": session.get("location", ""),
        "state": session.get("state", ""),
        "property_type": session.get(
            "property_type",
            ""
        ),
        "purpose": session.get(
            "purpose",
            ""
        ),
        "budget": session.get("budget"),
        "budget_text": session.get(
            "budget_text",
            ""
        ),
        "bedrooms": session.get("bedrooms"),
        "timeline": session.get(
            "timeline",
            ""
        ),
        "message": session.get(
            "message",
            ""
        ),
        "lead_quality": session.get(
            "lead_quality",
            ""
        ),
        "main_problem": session.get(
            "main_problem",
            ""
        ),
        "recommended_action": session.get(
            "recommended_action",
            ""
        ),
        "source": "real-estate-webhook",
        "property_images": session.get(
            "property_images",
            []
        )
    }

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=20
        )

        print(
            "n8n response:",
            response.status_code,
            response.text
        )

        if 200 <= response.status_code < 300:
            session["n8n_sent"] = True
            return True

        print(
            "n8n error:",
            response.status_code,
            response.text
        )

        return False

    except Exception as error:

        print(
            "n8n connection error:",
            repr(error)
        )

        return False


# =========================================================
# SAVE LEAD TO SUPABASE
# =========================================================

def save_to_supabase(
    session: Dict[str, Any]
) -> bool:

    if session.get("supabase_saved"):
        return True

    if not SUPABASE_URL:
        print(
            "Supabase error: SUPABASE_URL is missing"
        )
        return False

    if not SUPABASE_KEY:
        print(
            "Supabase error: SUPABASE_KEY is missing"
        )
        return False

    payload = {
        "name": session.get("name", ""),
        "email": session.get("email", ""),
        "phone": session.get("phone", ""),
        "location": session.get("location", ""),
        "property_type": session.get(
            "property_type",
            ""
        ),
        "purpose": session.get(
            "purpose",
            ""
        ),
        "budget": session.get("budget"),

        # IMPORTANT:
        # Chatbot uses "bedrooms".
        # Supabase column is "bedroom".
        "bedroom": session.get("bedrooms"),

        "timeline": session.get(
            "timeline",
            ""
        ),
        "message": session.get(
            "message",
            ""
        ),
        "lead_quality": session.get(
            "lead_quality",
            ""
        ),
        "main_problem": session.get(
            "main_problem",
            ""
        ),
        "recommended_action": session.get(
            "recommended_action",
            ""
        ),
        "source": "real-estate-chatbot"
    }

    property_images = session.get(
        "property_images",
        []
    )

    if property_images:
        payload["property_images"] = [
            image.get("url")
            for image in property_images
            if image.get("url")
        ]

    table_url = (
        SUPABASE_URL.rstrip("/")
        + "/rest/v1/"
        + SUPABASE_TABLE.replace(
            " ",
            "%20"
        )
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": (
            "Bearer "
            + SUPABASE_KEY
        ),
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    print("")
    print("========== SUPABASE INSERT ==========")
    print("URL:", table_url)
    print("Payload:", payload)

    try:

        response = requests.post(
            table_url,
            headers=headers,
            json=payload,
            timeout=20
        )

    except Exception as error:

        print(
            "Supabase connection error:",
            repr(error)
        )

        return False

    print(
        "Supabase status:",
        response.status_code
    )

    print(
        "Supabase response:",
        response.text
    )

    print("======================================")
    print("")

    if 200 <= response.status_code < 300:
        session["supabase_saved"] = True
        return True

    print(
        "Supabase error:",
        response.status_code,
        response.text
    )

    return False


# =========================================================
# CHAT ENDPOINT
# =========================================================

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
        session_id = create_session()

    if session_id not in sessions:
        sessions[session_id] = create_session(
            session_id
        )

    session = sessions[session_id]

    if "property_images" not in session:
        session["property_images"] = []

    if message:

        session["message"] = message

        update_lead(
            session,
            message
        )

    session["lead_quality"] = (
        calculate_lead_quality(
            session
        )
    )

    missing = next_missing_field(
        session
    )

    if missing is None:

        n8n_saved = send_to_n8n(
            session
        )

        supabase_saved = save_to_supabase(
            session
        )

        reply = (
            "Thank you! I have all the information I need. "
            "Our property team will review your request and "
            "contact you shortly."
        )

    else:

        n8n_saved = session.get(
            "n8n_sent",
            False
        )

        supabase_saved = session.get(
            "supabase_saved",
            False
        )

        if not any(
            session.get(field)
            for field in [
                "purpose",
                "location",
                "property_type",
                "budget",
                "timeline",
                "name",
                "phone",
                "email"
            ]
        ):

            reply = (
                "Welcome! I'm your real estate assistant. "
                "Are you looking to buy, rent, or invest?"
            )

        else:

            reply = QUESTIONS.get(
                missing,
                "Could you provide a little more information?"
            )

        session["last_asked"] = missing

    lead = {
        "name": session.get(
            "name",
            ""
        ),
        "email": session.get(
            "email",
            ""
        ),
        "phone": session.get(
            "phone",
            ""
        ),
        "location": session.get(
            "location",
            ""
        ),
        "property_type": session.get(
            "property_type",
            ""
        ),
        "purpose": session.get(
            "purpose",
            ""
        ),
        "budget": session.get(
            "budget"
        ),
        "bedrooms": session.get(
            "bedrooms"
        ),
        "timeline": session.get(
            "timeline",
            ""
        ),
        "lead_quality": session.get(
            "lead_quality",
            ""
        ),
        "property_images": session.get(
            "property_images",
            []
        )
    }

    return {
        "success": True,
        "session_id": session_id,
        "reply": reply,
        "lead": lead,
        "missing_field": missing,
        "lead_quality": session.get(
            "lead_quality",
            ""
        ),
        "integrations": {
            "n8n": {
                "sent": n8n_saved
            },
            "supabase": {
                "saved": supabase_saved
            }
        }
    }


# =========================================================
# DIRECT LEAD ENDPOINT
# =========================================================

@app.post("/api/v1/leads")
def create_lead(
    lead: LeadRequest
):

    session = {
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "location": lead.location,
        "state": lead.state,
        "property_type": lead.property_type,
        "purpose": lead.purpose,
        "budget": lead.budget,
        "budget_text": lead.budget_text,
        "bedrooms": lead.bedrooms,
        "timeline": lead.timeline,
        "message": lead.message,
        "lead_quality": lead.lead_quality,
        "main_problem": lead.main_problem,
        "recommended_action": lead.recommended_action,
        "source": lead.source,
        "property_images": [],
        "n8n_sent": False,
        "supabase_saved": False
    }

    n8n_saved = send_to_n8n(
        session
    )

    supabase_saved = save_to_supabase(
        session
    )

    return {
        "success": True,
        "message": "Lead processed",
        "lead": lead.dict(),
        "integrations": {
            "n8n": {
                "sent": n8n_saved
            },
            "supabase": {
                "saved": supabase_saved
            }
        }
    }