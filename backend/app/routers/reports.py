from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models import CitizenReport
from app.schemas import CitizenReportCreate, CitizenReportOut

router = APIRouter(prefix="/reports", tags=["Citizen Early Warning Reports"])

# Initial curated ground reports to provide populated contextual data
INITIAL_REPORTS = [
    {
        "latitude": 11.5305,
        "longitude": 76.1302,
        "location_name": "Chooralmala Road, Wayanad",
        "event_type": "water_seepage",
        "severity": "high",
        "description": "Muddy brown runoff emerging from upper tea garden slope cut. Drainage ditch overwhelmed.",
        "reporter_name": "Local Resident Association",
        "verified": True
    },
    {
        "latitude": 26.1510,
        "longitude": 91.7340,
        "location_name": "Narakasur Hill, Guwahati",
        "event_type": "slope_cracks",
        "severity": "critical",
        "description": "Fresh vertical fracture detected across hillside retaining embankment following 3 hours of rain.",
        "reporter_name": "Ward Safety Volunteer",
        "verified": True
    },
    {
        "latitude": 31.1090,
        "longitude": 77.1700,
        "location_name": "Summer Hill By-pass, Shimla",
        "event_type": "rockfall",
        "severity": "medium",
        "description": "Small loose boulders (30-50cm) dislodged onto downhill roadway. Single lane traffic blocked.",
        "reporter_name": "Highway Patrol",
        "verified": False
    },
    {
        "latitude": 27.0450,
        "longitude": 88.2610,
        "location_name": "Lebong Cart Road, Darjeeling",
        "event_type": "minor_slide",
        "severity": "high",
        "description": "Slumping of soil berm across 10-meter stretch behind tea stalls.",
        "reporter_name": "Civil Defense Volunteer",
        "verified": True
    }
]

@router.post("", response_model=CitizenReportOut, status_code=201)
async def submit_citizen_report(
    report_in: CitizenReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a crowd-sourced hazard observation:
    (slope cracks, water seepage, rockfall, minor mudslides, blocked culverts).
    Validates coordinate bounds and prevents silent ingestion failure.
    """
    report = CitizenReport(
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        location_name=report_in.location_name or "Reported Location",
        event_type=report_in.event_type,
        severity=report_in.severity.lower(),
        description=report_in.description,
        reporter_name=report_in.reporter_name or "Anonymous Citizen",
        verified=False
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

@router.get("", response_model=List[CitizenReportOut])
async def list_citizen_reports(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Returns recent crowdsourced reports for live map visualization and local triage."""
    stmt = select(CitizenReport).order_by(desc(CitizenReport.created_at)).limit(limit)
    if severity:
        stmt = stmt.where(CitizenReport.severity == severity.lower())
    
    result = await db.execute(stmt)
    reports = result.scalars().all()

    # If database is fresh/empty (e.g. initial run or after Render redeploy), seed initial items
    if not reports:
        for seed_data in INITIAL_REPORTS:
            new_rep = CitizenReport(**seed_data)
            db.add(new_rep)
        await db.commit()
        result = await db.execute(stmt)
        reports = result.scalars().all()

    return reports

@router.get("/stats")
async def get_report_statistics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Provides summary breakdown of citizen-reported hazards."""
    # Count by severity
    result = await db.execute(
        select(CitizenReport.severity, func.count(CitizenReport.id)).group_by(CitizenReport.severity)
    )
    severity_counts = dict(result.all())

    # Count by event type
    result2 = await db.execute(
        select(CitizenReport.event_type, func.count(CitizenReport.id)).group_by(CitizenReport.event_type)
    )
    event_counts = dict(result2.all())

    total = sum(severity_counts.values())

    return {
        "total_reports": total,
        "by_severity": severity_counts,
        "by_event_type": event_counts
    }
