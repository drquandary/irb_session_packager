from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models import (
    BIDSEvent,
    ImagingModality,
    IRBDocument,
    ParticipantPopulation,
    RiskLevel,
    SessionMetadata,
    SessionType,
    SOPDocument,
)


class TestModels:
    """Test cases for data models."""

    def test_session_metadata_valid(self):
        """Test valid session metadata creation."""
        metadata = SessionMetadata(
            session_id="test_session_001",
            study_name="Test Study",
            principal_investigator="Dr. Test",
            modality=ImagingModality.FMRI,
            session_type=SessionType.TASK_BASED,
            participant_population=ParticipantPopulation.HEALTHY_ADULTS,
            risk_level=RiskLevel.MINIMAL,
            duration_minutes=60,
            expected_participants=50,
        )

        assert metadata.session_id == "test_session_001"
        assert metadata.study_name == "Test Study"
        assert metadata.modality == ImagingModality.FMRI

    def test_session_metadata_invalid_session_id(self):
        """Test invalid session ID validation."""
        with pytest.raises(ValidationError):
            SessionMetadata(
                session_id="invalid session id!",
                study_name="Test Study",
                principal_investigator="Dr. Test",
                modality=ImagingModality.FMRI,
                session_type=SessionType.TASK_BASED,
                participant_population=ParticipantPopulation.HEALTHY_ADULTS,
                risk_level=RiskLevel.MINIMAL,
                duration_minutes=60,
                expected_participants=50,
            )

    def test_session_metadata_invalid_duration(self):
        """Test invalid duration validation."""
        with pytest.raises(ValidationError):
            SessionMetadata(
                session_id="test_session_001",
                study_name="Test Study",
                principal_investigator="Dr. Test",
                modality=ImagingModality.FMRI,
                session_type=SessionType.TASK_BASED,
                participant_population=ParticipantPopulation.HEALTHY_ADULTS,
                risk_level=RiskLevel.MINIMAL,
                duration_minutes=0,  # Invalid: must be >= 1
                expected_participants=50,
            )

    def test_bids_event_valid(self):
        """Test valid BIDS event creation."""
        event = BIDSEvent(
            onset=10.5,
            duration=2.0,
            trial_type="stimulus",
            response_time=1.2,
            accuracy=0.95,
            stimulus_file="stim1.jpg",
        )

        assert event.onset == 10.5
        assert event.trial_type == "stimulus"

    def test_bids_event_invalid_onset(self):
        """Test invalid onset validation."""
        with pytest.raises(ValidationError):
            BIDSEvent(
                onset=-1.0, duration=2.0, trial_type="stimulus"  # Invalid: must be >= 0
            )

    def test_sop_document_valid(self):
        """Test valid SOP document creation."""
        sop = SOPDocument(
            title="Test SOP",
            purpose="Test purpose",
            scope="Test scope",
            procedure_steps=["Step 1", "Step 2", "Step 3"],
        )

        assert sop.title == "Test SOP"
        assert len(sop.procedure_steps) == 3

    def test_irb_document_valid(self):
        """Test valid IRB document creation."""
        doc = IRBDocument(
            document_type="informed_consent",
            content="Test content for informed consent",
        )

        assert doc.document_type == "informed_consent"
        assert doc.version == "1.0"  # Default value

    def test_enum_values(self):
        """Test enum values are correct."""
        assert ImagingModality.FMRI.value == "fMRI"
        assert SessionType.TASK_BASED.value == "task_based"
        assert RiskLevel.MINIMAL.value == "minimal"
        assert ParticipantPopulation.HEALTHY_ADULTS.value == "healthy_adults"
