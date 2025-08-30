from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ImagingModality(str, Enum):
    """Supported imaging modalities for IRB sessions."""
    FMRI = "fMRI"
    EEG = "EEG"
    TMS = "TMS"
    MRI = "MRI"
    PET = "PET"
    MEG = "MEG"


class SessionType(str, Enum):
    """Types of research sessions."""
    RESTING_STATE = "resting_state"
    TASK_BASED = "task_based"
    STIMULATION = "stimulation"
    CLINICAL = "clinical"
    PILOT = "pilot"


class RiskLevel(str, Enum):
    """IRB risk assessment levels."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ParticipantPopulation(str, Enum):
    """Types of participant populations."""
    HEALTHY_ADULTS = "healthy_adults"
    CLINICAL = "clinical_population"
    CHILDREN = "children"
    ELDERLY = "elderly"
    PREGNANT = "pregnant"


class ConsentStatus(str, Enum):
    """Dynamic consent status options."""
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"


class ConsentType(str, Enum):
    """Types of consent permissions."""
    DATA_SHARING = "data_sharing"
    RECONTACT = "recontact"
    FUTURE_RESEARCH = "future_research"
    GENETIC_ANALYSIS = "genetic_analysis"
    COMMERCIAL_USE = "commercial_use"


class ComplianceStatus(str, Enum):
    """Compliance checking status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    PENDING = "pending"


class RiskCategory(str, Enum):
    """Risk assessment categories."""
    PHYSICAL = "physical"
    PSYCHOLOGICAL = "psychological"
    PRIVACY = "privacy"
    SOCIAL = "social"
    ECONOMIC = "economic"


class BIDSEvent(BaseModel):
    """BIDS-compliant event structure."""
    onset: float = Field(..., ge=0, description="Event onset time in seconds")
    duration: float = Field(..., ge=0, description="Event duration in seconds")
    trial_type: str = Field(..., description="Type of trial or condition")
    response_time: Optional[float] = Field(None, ge=0, description="Response time if applicable")
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="Accuracy score if applicable")
    stimulus_file: Optional[str] = Field(None, description="Path to stimulus file")
    
    @validator('onset', 'duration', 'response_time')
    def validate_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Time values must be non-negative')
        return v


class SessionMetadata(BaseModel):
    """Core session metadata for IRB and BIDS compliance."""
    session_id: str = Field(..., min_length=3, max_length=50, description="Unique session identifier")
    study_name: str = Field(..., min_length=3, max_length=100, description="Name of the research study")
    principal_investigator: str = Field(..., min_length=2, max_length=100, description="PI name")
    modality: ImagingModality = Field(..., description="Primary imaging modality")
    session_type: SessionType = Field(..., description="Type of research session")
    participant_population: ParticipantPopulation = Field(..., description="Target participant population")
    risk_level: RiskLevel = Field(..., description="IRB risk assessment level")
    duration_minutes: int = Field(..., ge=1, le=480, description="Session duration in minutes")
    expected_participants: int = Field(..., ge=1, le=10000, description="Expected number of participants")
    date_created: datetime = Field(default_factory=datetime.now)
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Session ID must be alphanumeric with underscores and hyphens only')
        return v


class IRBDocument(BaseModel):
    """IRB document structure."""
    document_type: str = Field(..., description="Type of IRB document")
    version: str = Field(default="1.0", description="Document version")
    content: str = Field(..., description="Document content")
    created_at: datetime = Field(default_factory=datetime.now)
    approved: bool = Field(default=False, description="IRB approval status")


class SOPDocument(BaseModel):
    """Standard Operating Procedure document."""
    title: str = Field(..., description="SOP title")
    version: str = Field(default="1.0", description="SOP version")
    purpose: str = Field(..., description="Purpose of the procedure")
    scope: str = Field(..., description="Scope of application")
    procedure_steps: List[str] = Field(..., description="Step-by-step procedure")
    safety_considerations: List[str] = Field(default_factory=list, description="Safety considerations")
    equipment_needed: List[str] = Field(default_factory=list, description="Required equipment")
    quality_control: List[str] = Field(default_factory=list, description="Quality control measures")


class SessionPackage(BaseModel):
    """Complete session package containing all generated documents."""
    session_metadata: SessionMetadata
    bids_events: List[BIDSEvent] = Field(default_factory=list)
    sop_documents: List[SOPDocument] = Field(default_factory=list)
    irb_documents: List[IRBDocument] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PackageRequest(BaseModel):
    """Request model for generating session packages."""
    session_metadata: SessionMetadata
    include_sop: bool = Field(default=True, description="Include SOP documents")
    include_irb: bool = Field(default=True, description="Include IRB documents")
    include_bids: bool = Field(default=True, description="Include BIDS templates")
    custom_events: Optional[List[BIDSEvent]] = Field(None, description="Custom BIDS events")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DynamicConsent(BaseModel):
    """Dynamic consent management model."""
    participant_id: str = Field(..., description="Unique participant identifier")
    consent_permissions: Dict[ConsentType, ConsentStatus] = Field(..., description="Consent permissions")
    language_preference: str = Field(default="en", description="Participant language preference")
    consent_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    withdrawal_date: Optional[datetime] = Field(None, description="Date of consent withdrawal")
    notes: Optional[str] = Field(None, description="Additional consent notes")


class RiskAssessment(BaseModel):
    """Enhanced risk assessment model."""
    risk_category: RiskCategory = Field(..., description="Category of risk")
    risk_level: RiskLevel = Field(..., description="Assessed risk level")
    probability: float = Field(..., ge=0, le=1, description="Risk probability (0-1)")
    severity: float = Field(..., ge=0, le=1, description="Risk severity (0-1)")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation strategies")
    calculated_score: Optional[float] = Field(None, description="Calculated risk score")


class ComplianceCheck(BaseModel):
    """Compliance checking result."""
    check_type: str = Field(..., description="Type of compliance check")
    status: ComplianceStatus = Field(..., description="Compliance status")
    details: str = Field(..., description="Detailed compliance information")
    recommendations: List[str] = Field(default_factory=list, description="Compliance recommendations")
    checked_at: datetime = Field(default_factory=datetime.now)


class RecruitmentPlan(BaseModel):
    """Equity-focused recruitment planning."""
    target_demographics: Dict[str, Any] = Field(..., description="Target demographic breakdowns")
    recruitment_strategies: List[str] = Field(..., description="Recruitment strategies")
    diversity_requirements: Optional[Dict[str, float]] = Field(None, description="NIH diversity requirements")
    estimated_timeline: Optional[str] = Field(None, description="Estimated recruitment timeline")
    budget_considerations: Optional[Dict[str, float]] = Field(None, description="Budget considerations")


class AuditEntry(BaseModel):
    """Audit trail entry for version control."""
    entry_id: str = Field(..., description="Unique audit entry ID")
    session_id: str = Field(..., description="Associated session ID")
    action: str = Field(..., description="Action performed")
    user_id: str = Field(..., description="User who performed the action")
    timestamp: datetime = Field(default_factory=datetime.now)
    changes: Dict[str, Any] = Field(default_factory=dict, description="Changes made")
    version: str = Field(..., description="Document version")


class ParticipantCommunication(BaseModel):
    """Participant communication tracking."""
    participant_id: str = Field(..., description="Participant identifier")
    communication_type: str = Field(..., description="Type of communication")
    message_content: str = Field(..., description="Message content")
    sent_at: datetime = Field(default_factory=datetime.now)
    delivery_status: str = Field(default="pending", description="Delivery status")
    irb_approved: bool = Field(default=False, description="IRB approval status for communication")
