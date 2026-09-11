from fastapi import APIRouter

from backend.models.lead import Lead
from backend.services.n8n_service import send_lead_to_n8n


router = APIRouter(
    prefix="/api/v1",
    tags=["Leads"]
)


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