from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class CoordinateQuery(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate between -90 and 90")
    longitude: float = Field(..., description="Longitude coordinate between -180 and 180")
    location_name: Optional[str] = Field(None, description="Optional city or landmark label")

    @field_validator("latitude")
    @classmethod
    def check_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be strictly between -90.0 and 90.0 degrees.")
        return round(v, 6)

    @field_validator("longitude")
    @classmethod
    def check_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be strictly between -180.0 and 180.0 degrees.")
        return round(v, 6)

class WeatherData(BaseModel):
    rainfall_24h: float = Field(..., description="Cumulative 24-hour precipitation (mm)")
    rainfall_72h: float = Field(..., description="Cumulative 72-hour precipitation (mm)")
    soil_moisture: float = Field(..., description="Estimated surface soil moisture percentage (0-100%)")
    temperature_2m: Optional[float] = Field(None, description="Current ambient temperature (°C)")
    relative_humidity: Optional[float] = Field(None, description="Relative humidity (%)")
    dew_point_2m: Optional[float] = Field(None, description="Dew point temperature (°C)")
    surface_pressure: Optional[float] = Field(None, description="Surface atmospheric pressure (hPa)")
    wind_speed_10m: Optional[float] = Field(None, description="Surface wind speed (m/s)")
    wind_gusts_10m: Optional[float] = Field(None, description="Peak wind gust speed (m/s)")
    cape: Optional[float] = Field(None, description="Convective Available Potential Energy (J/kg)")
    provider: str = Field(..., description="Source of weather data")
    is_fallback: bool = Field(False)
    status_note: Optional[str] = None

class TerrainData(BaseModel):
    elevation: float = Field(..., description="Surface elevation in meters above sea level")
    slope: float = Field(..., description="Estimated terrain inclination angle in degrees (0-90°)")
    provider: str = Field(..., description="Source of digital elevation data")
    is_fallback: bool = Field(False)
    status_note: Optional[str] = None

class HistoricalData(BaseModel):
    historical_landslide_count: int = Field(..., description="Recorded historical events in regional radius")
    catalog_source: str = Field("NASA COOLR & GSI Catalog")
    provider: str = Field("NASA COOLR & GSI Catalog", description="Source of historical records")
    notable_events: List[str] = Field(default_factory=list)
    is_fallback: bool = Field(False)

# --- STEP 2 IN PDF: ATMOSPHERIC PRECURSORS ---
class AtmosphericPrecursors(BaseModel):
    iwv: float = Field(..., description="Integrated Water Vapour (total column atmospheric moisture in mm)")
    cape: float = Field(..., description="Convective Available Potential Energy (air parcel buoyant energy in J/kg)")
    cin: float = Field(..., description="Convective Inhibition (atmospheric lid stopping premature rising in J/kg)")
    low_level_convergence: float = Field(..., description="Low-level wind convergence forcing air upward (10^-5 s^-1)")
    wind_shear: float = Field(..., description="Vertical wind shear / velocity differential (m/s)")
    ctt_drop_rate: float = Field(..., description="Cloud Top Temperature cooling rate (°C/hr)")
    qpe_rate: float = Field(..., description="Quantitative Precipitation Estimation instant rain rate (mm/hr)")
    soil_saturation: float = Field(..., description="Topsoil volumetric saturation (%)")
    slope_angle: float = Field(..., description="Topographical slope angle (degrees)")

# --- STEP 3 & 5 IN PDF: MULTI-TASK HAZARD HEAD & XAI ATTRIBUTION ---
class XAIFactor(BaseModel):
    factor_name: str
    contribution_pct: float
    description: str

class HazardRiskOutput(BaseModel):
    hazard_type: str = Field(..., description="thunderstorm | cloudburst | flash_flood | landslide")
    hazard_title: str
    probability: float = Field(..., description="Estimated occurrence probability (0.0 to 1.0)")
    risk_level: str = Field(..., description="Low | Moderate | High | Severe")
    alert_color: str = Field(..., description="Hex color token")
    primary_warning_sign: str = Field(..., description="Key physical precursor driving the alert")
    model_provenance: str = Field("Prototype baseline", description="'Prototype baseline' for rule heads or 'Trained ML Model' for trained models")
    xai_breakdown: List[XAIFactor] = Field(default_factory=list, description="Baseline feature contribution weights")
    timeline_6h: List[Dict[str, Any]] = Field(default_factory=list, description="6-hour forward risk trajectory (T+1h to T+6h)")

# --- STEP 6 IN PDF: COMMON ALERTING PROTOCOL (CAP) SCHEMA ---
class CAPAlert(BaseModel):
    identifier: str
    sender: str = "GeoShield-NDMA-IMD-EarlyWarning"
    sent: datetime
    status: str = "Actual"
    msg_type: str = "Alert"
    scope: str = "Public"
    event: str
    urgency: str  # Immediate, Expected, Future
    severity: str  # Extreme, Severe, Moderate, Minor
    certainty: str  # Observed, Likely, Possible
    headline: str
    description: str
    instruction: str
    area_desc: str
    cap_xml_url: Optional[str] = None

# Comprehensive Multi-Hazard Response
class MultiHazardAssessmentResponse(BaseModel):
    latitude: float
    longitude: float
    location_name: str
    is_coastal: bool
    coast_region: Optional[str] = None
    is_hilly: bool = False
    mountain_range: Optional[str] = None
    terrain_type: str = "Hilly / Mountainous"
    terrain_badge: Optional[str] = None
    
    # Atmospheric Precursors (Step 2 in PDF)
    precursors: AtmosphericPrecursors
    
    # The 4 Multi-Task Prediction Heads (Step 3 in PDF)
    hazards: Dict[str, HazardRiskOutput]
    
    # Overall synthesized status
    highest_risk_hazard: str
    overall_alert_level: str
    overall_alert_color: str
    
    # Common Alerting Protocol Notice (Step 6 in PDF)
    cap_alert: Optional[CAPAlert] = None
    # Per-hazard independent alerts (Item G)
    hazard_alerts: Dict[str, CAPAlert] = Field(default_factory=dict, description="Active alerts fired independently per-hazard")
    
    # Data Provenance and Transparency Panel (Item I)
    data_provenance: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Live vs fallback transparency matrix")
    
    advisory: str
    action_items: List[str]
    is_demo: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- VERIFICATION METRICS SCHEMAS (POD, FAR, CSI, HSS) ---
class ContingencyTable(BaseModel):
    hits: int = Field(..., description="True Positives (TP): Event occurred and warning alert issued")
    false_alarms: int = Field(..., description="False Positives (FP): No event occurred but alert issued")
    misses: int = Field(..., description="False Negatives (FN): Event occurred but no alert issued")
    correct_negatives: int = Field(..., description="True Negatives (TN): No event occurred and no alert issued")
    total_evaluations: int

class VerificationMetrics(BaseModel):
    hazard_type: str = Field(..., description="all | thunderstorm | cloudburst | flash_flood | landslide")
    hazard_title: str
    pod: float = Field(..., description="Probability of Detection / Destruction (TP / [TP + FN]), range 0.0..1.0")
    pod_pct: float = Field(..., description="POD expressed as percentage")
    far: float = Field(..., description="False Alarm Rate/Ratio (FP / [TP + FP]), range 0.0..1.0")
    far_pct: float = Field(..., description="FAR expressed as percentage")
    csi: float = Field(..., description="Critical Success Index / Rate (TP / [TP + FN + FP]), range 0.0..1.0")
    csi_pct: float = Field(..., description="CSI expressed as percentage")
    hss: float = Field(..., description="Heidke Skill Score (-1.0..1.0), measuring skill above chance")
    bias_score: float = Field(..., description="Frequency Bias ([TP + FP] / [TP + FN])")
    accuracy: float = Field(..., description="Overall Accuracy ([TP + TN] / Total)")
    contingency_table: ContingencyTable
    description: str
    benchmark_standard: str

class SystemVerificationSummary(BaseModel):
    overall: VerificationMetrics
    hazard_breakdown: Dict[str, VerificationMetrics]
    explanation: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Legacy schema compatibility
class ContributingFactor(BaseModel):
    factor: str
    value: float
    unit: str
    contribution_weight: float
    description: str

class RiskAssessmentResponse(BaseModel):
    latitude: float
    longitude: float
    location_name: str
    ml_probability: float
    baseline_risk_score: float
    risk_level: str
    alert_color: str
    weather: WeatherData
    terrain: TerrainData
    history: HistoricalData
    primary_factors: List[ContributingFactor]
    advisory: str
    recommended_actions: List[str]
    is_demo: bool = False
    mode_label: str = "LIVE DATA ASSESSMENT"
    disclaimer: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DemoEscalationStep(BaseModel):
    step_number: int
    title: str
    stage_name: str
    description: str
    rainfall_24h: float
    rainfall_72h: float
    soil_moisture: float
    slope: float
    elevation: float
    historical_count: int
    ml_probability: float
    baseline_risk_score: float
    risk_level: str
    alert_color: str
    is_demo: bool = True
    mode_label: str = "DEMO SCENARIO"

class CitizenReportCreate(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = "Reported Location"
    event_type: str = Field(..., description="Event observed: 'slope_cracks', 'rockfall', 'minor_slide', 'water_seepage', 'drain_blockage', 'flash_flood', 'cloudburst', 'severe_storm'")
    severity: str = Field("medium", description="'low', 'medium', 'high', 'critical'")
    description: Optional[str] = ""
    reporter_name: Optional[str] = "Concerned Citizen"

    @field_validator("latitude")
    @classmethod
    def check_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be strictly between -90.0 and 90.0 degrees.")
        return round(v, 6)

    @field_validator("longitude")
    @classmethod
    def check_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be strictly between -180.0 and 180.0 degrees.")
        return round(v, 6)

class CitizenReportOut(BaseModel):
    id: int
    latitude: float
    longitude: float
    location_name: str
    event_type: str
    severity: str
    description: Optional[str]
    reporter_name: str
    created_at: datetime
    verified: bool

    class Config:
        from_attributes = True

class ModelRetrainRequest(BaseModel):
    n_samples: int = Field(5000, ge=1000, le=50000)
    learning_rate: float = Field(0.05, ge=0.001, le=0.5)
    n_estimators: int = Field(200, ge=50, le=1000)
    max_depth: int = Field(5, ge=2, le=15)
    random_state: int = Field(42)

class ModelRetrainResponse(BaseModel):
    status: str
    message: str
    samples_trained: int
    classification_report: Dict[str, Any]
    verification_metrics: Optional[VerificationMetrics] = None
    feature_importance: Dict[str, float]
    saved_path: str

