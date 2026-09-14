from typing import Optional, List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.agent.graph import run_investigation

router = APIRouter(prefix="/investigations", tags=["Investigations"])


class InvestigationRequest(BaseModel):
    transaction_id: str
    complaint: Optional[str] = ""
    agent_mode: Optional[str] = "improved"  # "baseline" or "improved"
    evidence: Optional[List[Dict[str, Any]]] = None


@router.post("/analyze")
def analyze_transaction(request: InvestigationRequest):
    result = run_investigation(
        transaction_id=request.transaction_id,
        complaint=request.complaint or "",
        agent_mode=request.agent_mode or "improved",
        custom_evidence=request.evidence
    )
    return result