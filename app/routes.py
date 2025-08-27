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
    ImagingModality, SessionType, RiskLevel, ParticipantPopulation, BIDSEvent
)
from .packager import SessionPackager

router = APIRouter()

# Initialize the session packager
packager = SessionPackager()


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
