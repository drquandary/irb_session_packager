import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_serves_html():
    """Test that root serves HTML interface."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "IRB Session Packager" in response.text


def test_api_root():
    """Test API root endpoint."""
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json().get("detail") == "IRB and Session Packager API"


def test_health():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "service" in data


def test_get_modalities():
    """Test modalities endpoint."""
    response = client.get("/api/modalities")
    assert response.status_code == 200
    data = response.json()
    assert "modalities" in data
    assert "session_types" in data
    assert "risk_levels" in data
    assert "populations" in data
    assert "fMRI" in data["modalities"]


def test_create_package():
    """Test package creation."""
    payload = {
        "session_metadata": {
            "session_id": "test_session_001",
            "study_name": "Test Study",
            "principal_investigator": "Dr. Test",
            "modality": "fMRI",
            "session_type": "task_based",
            "participant_population": "healthy_adults",
            "risk_level": "minimal",
            "duration_minutes": 60,
            "expected_participants": 20,
        },
        "include_sop": True,
        "include_irb": True,
        "include_bids": True,
    }

    response = client.post("/api/create-package", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_001"
    assert "package_summary" in data
    assert "created_at" in data


def test_create_package_invalid_data():
    """Test package creation with invalid data."""
    payload = {
        "session_metadata": {
            "session_id": "",  # Invalid empty session ID
            "study_name": "Test Study",
            "principal_investigator": "Dr. Test",
            "modality": "fMRI",
            "session_type": "task_based",
            "participant_population": "healthy_adults",
            "risk_level": "minimal",
            "duration_minutes": 60,
            "expected_participants": 20,
        },
        "include_sop": True,
        "include_irb": True,
        "include_bids": True,
    }

    response = client.post("/api/create-package", json=payload)
    assert response.status_code == 422  # Validation error


def test_package_summary_existing():
    """Test getting summary of existing package."""
    # First create a package
    payload = {
        "session_metadata": {
            "session_id": "test_summary_001",
            "study_name": "Test Summary Study",
            "principal_investigator": "Dr. Summary",
            "modality": "EEG",
            "session_type": "resting_state",
            "participant_population": "clinical_population",
            "risk_level": "low",
            "duration_minutes": 30,
            "expected_participants": 15,
        },
        "include_sop": True,
        "include_irb": True,
        "include_bids": True,
    }

    create_response = client.post("/api/create-package", json=payload)
    assert create_response.status_code == 200

    # Now get summary
    response = client.get("/api/package-summary/test_summary_001")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_summary_001"
    assert data["modality"] == "EEG"
    assert "document_counts" in data


def test_package_summary_nonexistent():
    """Test getting summary of nonexistent package."""
    response = client.get("/api/package-summary/nonexistent_123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_export_package_existing():
    """Test exporting existing package."""
    # First create a package
    payload = {
        "session_metadata": {
            "session_id": "test_export_001",
            "study_name": "Test Export Study",
            "principal_investigator": "Dr. Export",
            "modality": "TMS",
            "session_type": "stimulation",
            "participant_population": "healthy_adults",
            "risk_level": "moderate",
            "duration_minutes": 45,
            "expected_participants": 10,
        },
        "include_sop": True,
        "include_irb": True,
        "include_bids": True,
    }

    create_response = client.post("/api/create-package", json=payload)
    assert create_response.status_code == 200

    # Now export
    export_payload = {"session_id": "test_export_001", "formats": ["json", "pdf"]}

    response = client.post("/api/export-package", json=export_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_export_001"
    assert "exported_files" in data


def test_export_package_nonexistent():
    """Test exporting nonexistent package."""
    export_payload = {"session_id": "nonexistent_export_123", "formats": ["json"]}

    response = client.post("/api/export-package", json=export_payload)
    assert response.status_code == 404


def test_download_package_existing():
    """Test downloading existing package."""
    # First create a package
    payload = {
        "session_metadata": {
            "session_id": "test_download_001",
            "study_name": "Test Download Study",
            "principal_investigator": "Dr. Download",
            "modality": "MRI",
            "session_type": "clinical",
            "participant_population": "elderly",
            "risk_level": "high",
            "duration_minutes": 120,
            "expected_participants": 5,
        },
        "include_sop": True,
        "include_irb": True,
        "include_bids": True,
    }

    create_response = client.post("/api/create-package", json=payload)
    assert create_response.status_code == 200

    # Now download
    response = client.get("/api/download-package/test_download_001?format=json")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


def test_download_package_nonexistent():
    """Test downloading nonexistent package."""
    response = client.get("/api/download-package/nonexistent_download_123?format=json")
    assert response.status_code == 404


def test_validate_package():
    """Test package validation."""
    payload = {
        "session_metadata": {
            "session_id": "test_validate_001",
            "study_name": "Test Validate Study",
            "principal_investigator": "Dr. Validate",
            "modality": "PET",
            "session_type": "pilot",
            "participant_population": "children",
            "risk_level": "low",
            "duration_minutes": 90,
            "expected_participants": 25,
        },
        "include_sop": True,
        "include_irb": True,
        "include_bids": True,
    }

    response = client.post("/api/validate-package", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert isinstance(data["valid"], bool)


def test_list_packages():
    """Test listing packages."""
    response = client.get("/api/packages")
    assert response.status_code == 200
    data = response.json()
    assert "packages" in data
    assert isinstance(data["packages"], list)


def test_delete_package_existing():
    """Test deleting existing package."""
    # First create a package
    payload = {
        "session_metadata": {
            "session_id": "test_delete_001",
            "study_name": "Test Delete Study",
            "principal_investigator": "Dr. Delete",
            "modality": "MEG",
            "session_type": "resting_state",
            "participant_population": "pregnant",
            "risk_level": "low",
            "duration_minutes": 20,
            "expected_participants": 8,
        },
        "include_sop": True,
        "include_irb": True,
        "include_bids": True,
    }

    create_response = client.post("/api/create-package", json=payload)
    assert create_response.status_code == 200

    # Now delete
    response = client.delete("/api/package/test_delete_001")
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


def test_delete_package_nonexistent():
    """Test deleting nonexistent package."""
    response = client.delete("/api/package/nonexistent_delete_123")
    assert response.status_code == 404
