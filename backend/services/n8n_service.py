import requests
from fastapi import HTTPException

from backend.core.config import N8N_WEBHOOK_URL


def send_lead_to_n8n(lead_data: dict):
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=lead_data,
            timeout=10
        )

        response.raise_for_status()

        return response

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="n8n webhook request timed out"
        )

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to n8n"
        )

    except requests.exceptions.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"n8n request failed: {error}"
        )