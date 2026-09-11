from pydantic import BaseModel, EmailStr, Field


class Lead(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=7)
    location: str = Field(..., min_length=1)
    property_type: str = Field(..., min_length=1)
    budget: float = Field(..., ge=0)
    bedrooms: int = Field(..., ge=0)
    purpose: str = Field(..., min_length=1)
    timeline: str = Field(..., min_length=1)
    message: str = ""
    lead_quality: str = ""
    main_problem: str = ""
    recommended_action: str = ""
    source: str = ""