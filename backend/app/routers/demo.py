from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas import DemoEscalationStep, RiskAssessmentResponse
from app.services.demo_service import demo_service

router = APIRouter(prefix="/demo", tags=["Demo Mode Escalation"])

@router.get("/steps", response_model=List[DemoEscalationStep])
async def list_demo_steps():
    """
    Returns the complete 5-stage severe-weather escalation scenario.
    Shows the step-by-step transition:
    moisture ↑ → instability ↑ → precipitation ↑ → flash flood/landslide risk ↑ → HIGH ALERT.
    """
    return demo_service.get_all_demo_steps()

@router.get("/step/{step_number}", response_model=RiskAssessmentResponse)
async def get_demo_step_assessment(step_number: int):
    """
    Returns full risk assessment representation for a given demonstration step (1 through 5).
    Exemplifies strict separation between live and simulated demo data.
    """
    if step_number < 1 or step_number > 5:
        raise HTTPException(
            status_code=400,
            detail="Demo step must be an integer between 1 and 5."
        )
    return demo_service.get_step_assessment(step_number)
