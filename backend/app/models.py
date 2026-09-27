from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text
from app.database import Base

class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location_name = Column(String(255), default="Unknown Location")
    event_type = Column(String(100), nullable=False)  # slope_cracks, rockfall, minor_slide, water_seepage, etc.
    severity = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    description = Column(Text, nullable=True)
    reporter_name = Column(String(100), default="Anonymous Citizen")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    verified = Column(Boolean, default=False)

class RiskAssessmentLog(Base):
    __tablename__ = "risk_assessment_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location_name = Column(String(255), nullable=True)
    ml_probability = Column(Float, nullable=False)
    baseline_risk = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)
    rainfall_24h = Column(Float, nullable=False)
    rainfall_72h = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    slope = Column(Float, nullable=False)
    elevation = Column(Float, nullable=False)
    historical_count = Column(Integer, default=0)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
