from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json
import tempfile
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import (
    SessionMetadata, PackageRequest, SessionPackage, 
    ImagingModality, SessionType, RiskLevel, ParticipantPopulation, BIDSEvent,
    DynamicConsent, ConsentType, ConsentStatus, RiskAssessment, RiskCategory,
    ComplianceCheck, RecruitmentPlan, ParticipantCommunication
)
from .packager import SessionPackager
from .consent_manager import ConsentManager
from .audit_manager import AuditManager

router = APIRouter()

# Initialize the session packager, consent manager, and audit manager
packager = SessionPackager()
consent_manager = ConsentManager()
audit_manager = AuditManager()


class SessionCreateRequest(BaseModel):
    """Request model for creating a session package."""
    session_metadata: SessionMetadata
    include_sop: bool = True
    include_irb: bool = True
    include_bids: bool = True
    custom_events: Optional[List[BIDSEvent]] = None
    additional_metadata: Optional[Dict[str, Any]] = None


class SessionCreateResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    package_summary: Dict[str, Any]
    created_at: datetime


class ExportRequest(BaseModel):
    """Request model for exporting packages."""
    session_id: str
    formats: List[str] = ["json", "pdf", "docx", "bids", "zip"]
    output_dir: Optional[str] = None


class ConsentRequest(BaseModel):
    """Request model for consent management."""
    participant_id: str
    consent_permissions: Dict[ConsentType, ConsentStatus]
    language_preference: str = "en"
    notes: Optional[str] = None


class RiskCalculationRequest(BaseModel):
    """Request model for risk calculation."""
    session_metadata: SessionMetadata
    risk_assessments: List[RiskAssessment]


class ComplianceCheckRequest(BaseModel):
    """Request model for compliance checking."""
    session_metadata: SessionMetadata
    document_content: str


class RecruitmentPlanRequest(BaseModel):
    """Request model for recruitment planning."""
    session_metadata: SessionMetadata
    target_demographics: Dict[str, Any]


@router.get('/health')
async def health():
    """Health check endpoint."""
    return {'status': 'ok', 'service': 'IRB Session Packager'}


@router.get('/modalities')
async def get_modalities():
    """Get available imaging modalities."""
    return {
        "modalities": [modality.value for modality in ImagingModality],
        "session_types": [stype.value for stype in SessionType],
        "risk_levels": [risk.value for risk in RiskLevel],
        "populations": [pop.value for pop in ParticipantPopulation]
    }


@router.post('/create-package')
async def create_package(request: SessionCreateRequest):
    """Create a new session package."""
    try:
        # Create package request
        package_request = PackageRequest(
            session_metadata=request.session_metadata,
            include_sop=request.include_sop,
            include_irb=request.include_irb,
            include_bids=request.include_bids,
            custom_events=request.custom_events,
            additional_metadata=request.additional_metadata
        )
        
        # Create the package
        session_package = packager.create_session_package(package_request)
        
        # Validate the package
        validation = packager.validate_package(session_package)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Package validation failed: {validation['errors']}"
            )
        
        # Get summary
        summary = packager.get_package_summary(session_package)
        
        return SessionCreateResponse(
            session_id=session_package.session_metadata.session_id,
            package_summary=summary,
            created_at=session_package.created_at
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/export-package')
async def export_package(request: ExportRequest, background_tasks: BackgroundTasks):
    """Export a session package in various formats."""
    try:
        # Try to load existing package from storage
        session_package = packager.load_package(request.session_id)

        if session_package is None:
            raise HTTPException(
                status_code=404,
                detail=f"Package with session ID '{request.session_id}' not found"
            )

        # Determine output directory
        output_dir = Path(request.output_dir) if request.output_dir else Path("./output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export package
        exported_files = packager.export_package(
            session_package,
            output_dir,
            request.formats
        )

        # Convert paths to strings for JSON serialization
        exported_files_str = {k: str(v) for k, v in exported_files.items()}

        return {
            "session_id": request.session_id,
            "exported_files": exported_files_str,
            "export_time": datetime.now()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/download-package/{session_id}')
async def download_package(session_id: str, format: str = "zip"):
    """Download a session package."""
    try:
        # Load existing package from storage
        session_package = packager.load_package(session_id)

        if session_package is None:
            raise HTTPException(
                status_code=404,
                detail=f"Package with session ID '{session_id}' not found"
            )

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            if format == "zip":
                zip_path = packager._export_zip(session_package, temp_path)
                return FileResponse(
                    path=str(zip_path),
                    filename=f"{session_id}_package.zip",
                    media_type="application/zip"
                )
            elif format == "json":
                json_path = packager._export_json(session_package, temp_path)
                return FileResponse(
                    path=str(json_path),
                    filename=f"{session_id}_package.json",
                    media_type="application/json"
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/package-summary/{session_id}')
async def get_package_summary(session_id: str):
    """Get a summary of a session package."""
    try:
        # Load existing package from storage
        session_package = packager.load_package(session_id)

        if session_package is None:
            raise HTTPException(
                status_code=404,
                detail=f"Package with session ID '{session_id}' not found"
            )

        summary = packager.get_package_summary(session_package)
        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/validate-package')
async def validate_package(request: SessionCreateRequest):
    """Validate a session package before creation."""
    try:
        package_request = PackageRequest(
            session_metadata=request.session_metadata,
            include_sop=request.include_sop,
            include_irb=request.include_irb,
            include_bids=request.include_bids,
            custom_events=request.custom_events,
            additional_metadata=request.additional_metadata
        )

        session_package = packager.create_session_package(package_request, save_to_storage=False)
        validation = packager.validate_package(session_package)

        return validation

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/packages')
async def list_packages():
    """List all saved session packages."""
    try:
        packages = packager.list_packages()
        return {"packages": packages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/package/{session_id}')
async def delete_package(session_id: str):
    """Delete a session package."""
    try:
        success = packager.delete_package(session_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Package with session ID '{session_id}' not found"
            )
        return {"message": f"Package '{session_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced IRB features

@router.post('/consent/create')
async def create_consent(request: ConsentRequest):
    """Create or update dynamic consent for a participant."""
    try:
        consent = DynamicConsent(
            participant_id=request.participant_id,
            consent_permissions=request.consent_permissions,
            language_preference=request.language_preference,
            notes=request.notes
        )
        
        success = consent_manager.create_consent(consent)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create consent")
        
        return {"message": "Consent created successfully", "participant_id": request.participant_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/consent/{participant_id}')
async def get_consent(participant_id: str):
    """Get consent information for a participant."""
    try:
        consent = consent_manager.get_consent(participant_id)
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        return consent
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/consent/{participant_id}/update')
async def update_consent_status(participant_id: str, consent_type: ConsentType, new_status: ConsentStatus):
    """Update specific consent permission status."""
    try:
        success = consent_manager.update_consent_status(participant_id, consent_type, new_status)
        if not success:
            raise HTTPException(status_code=404, detail="Consent not found or update failed")
        
        return {"message": f"Consent status updated for {consent_type.value}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/consent/{participant_id}/withdraw')
async def withdraw_consent(participant_id: str, reason: Optional[str] = None):
    """Withdraw all consent permissions for a participant."""
    try:
        success = consent_manager.withdraw_all_consent(participant_id, reason)
        if not success:
            raise HTTPException(status_code=404, detail="Consent not found or withdrawal failed")
        
        return {"message": "All consent permissions withdrawn"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/consent/{participant_id}/check-validity')
async def check_consent_validity(participant_id: str, request: SessionCreateRequest):
    """Check if participant consent is valid for a session."""
    try:
        validity = consent_manager.check_consent_validity(participant_id, request.session_metadata)
        return validity
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/consent/report')
async def get_consent_report():
    """Generate consent status report."""
    try:
        report = consent_manager.generate_consent_report()
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/risk/calculate')
async def calculate_risk_score(request: RiskCalculationRequest):
    """Calculate comprehensive risk score for a session."""
    try:
        risk_score = packager.irb_generator.calculate_risk_score(
            request.session_metadata, 
            request.risk_assessments
        )
        return risk_score
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/compliance/check')
async def check_compliance(request: ComplianceCheckRequest):
    """Perform automated compliance checking on IRB documents."""
    try:
        compliance_checks = packager.irb_generator.check_compliance(
            request.session_metadata,
            request.document_content
        )
        
        return {
            "compliance_checks": compliance_checks,
            "overall_status": "compliant" if all(
                check.status == ComplianceStatus.COMPLIANT for check in compliance_checks
            ) else "needs_review"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/recruitment/plan')
async def generate_recruitment_plan(request: RecruitmentPlanRequest):
    """Generate equity-focused recruitment plan."""
    try:
        recruitment_plan = packager.irb_generator.generate_recruitment_plan(
            request.session_metadata,
            request.target_demographics
        )
        
        return recruitment_plan
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/audit/trail/{session_id}')
async def get_audit_trail(session_id: str):
    """Get complete audit trail for a session."""
    try:
        audit_trail = audit_manager.get_audit_trail(session_id)
        return {"session_id": session_id, "audit_entries": audit_trail}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/audit/document-versions/{session_id}/{document_type}')
async def get_document_versions(session_id: str, document_type: str):
    """Get all versions of a specific document."""
    try:
        versions = audit_manager.get_document_versions(session_id, document_type)
        return {
            "session_id": session_id,
            "document_type": document_type,
            "versions": versions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/audit/report')
async def generate_audit_report(session_id: Optional[str] = None):
    """Generate comprehensive audit report."""
    try:
        report = audit_manager.generate_audit_report(session_id=session_id)
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/communication/log')
async def log_participant_communication(communication: ParticipantCommunication):
    """Log participant communication for compliance tracking."""
    try:
        success = consent_manager.log_communication(communication)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to log communication")
        
        return {"message": "Communication logged successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/communication/history/{participant_id}')
async def get_communication_history(participant_id: str):
    """Get communication history for a participant."""
    try:
        history = consent_manager.get_communication_history(participant_id)
        return {"participant_id": participant_id, "communications": history}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/integrations/apis')
async def get_integration_apis():
    """Get available integration APIs and their status."""
    # Placeholder for integration APIs like ezBIDS, OpenNeuro, etc.
    return {
        "available_integrations": [
            {
                "name": "ezBIDS",
                "description": "BIDS validation and organization",
                "status": "placeholder",
                "endpoint": "/integrations/ezbids"
            },
            {
                "name": "OpenNeuro",
                "description": "Open neuroscience data repository",
                "status": "placeholder", 
                "endpoint": "/integrations/openneuro"
            },
            {
                "name": "brainlife.io",
                "description": "Cloud platform for neuroscience",
                "status": "placeholder",
                "endpoint": "/integrations/brainlife"
            },
            {
                "name": "InformGen",
                "description": "AI-assisted informed consent generation",
                "status": "placeholder",
                "endpoint": "/integrations/informgen"
            }
        ]
    }


@router.post('/ai/mock-review')
async def ai_mock_review(request: SessionCreateRequest):
    """AI mock reviewer for IRB submissions (placeholder)."""
    try:
        # Placeholder for AI mock reviewer functionality
        session_package = packager.create_session_package(
            PackageRequest(
                session_metadata=request.session_metadata,
                include_sop=request.include_sop,
                include_irb=request.include_irb,
                include_bids=request.include_bids,
                custom_events=request.custom_events,
                additional_metadata=request.additional_metadata
            ),
            save_to_storage=False
        )
        
        # Mock AI review comments
        mock_comments = [
            {
                "section": "informed_consent",
                "comment": "Consider adding more specific information about data retention period",
                "severity": "minor",
                "suggestion": "Specify exact number of years data will be retained"
            },
            {
                "section": "risk_assessment", 
                "comment": "Risk assessment appears comprehensive for the proposed methodology",
                "severity": "none",
                "suggestion": None
            },
            {
                "section": "recruitment",
                "comment": "Recruitment plan meets diversity requirements",
                "severity": "none", 
                "suggestion": None
            }
        ]
        
        return {
            "session_id": request.session_metadata.session_id,
            "ai_review_comments": mock_comments,
            "overall_assessment": "Ready for IRB submission with minor revisions",
            "estimated_approval_likelihood": 0.85,
            "generated_at": datetime.now()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
