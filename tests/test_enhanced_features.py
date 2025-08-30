"""Tests for enhanced IRB Session Packager features."""

import pytest
from datetime import datetime
from app.models import (
    DynamicConsent, ConsentType, ConsentStatus, RiskAssessment, 
    RiskCategory, RiskLevel, ComplianceCheck, ComplianceStatus,
    SessionMetadata, ImagingModality, SessionType, ParticipantPopulation
)
from app.consent_manager import ConsentManager
from app.irb_generator import IRBGenerator


class TestEnhancedFeatures:
    """Test enhanced IRB features."""
    
    def test_dynamic_consent_model(self):
        """Test dynamic consent model creation and validation."""
        consent = DynamicConsent(
            participant_id="test_001",
            consent_permissions={
                ConsentType.DATA_SHARING: ConsentStatus.ACTIVE,
                ConsentType.RECONTACT: ConsentStatus.ACTIVE,
                ConsentType.FUTURE_RESEARCH: ConsentStatus.PENDING
            },
            language_preference="en",
            notes="Test consent"
        )
        
        assert consent.participant_id == "test_001"
        assert consent.consent_permissions[ConsentType.DATA_SHARING] == ConsentStatus.ACTIVE
        assert consent.language_preference == "en"
    
    def test_risk_assessment_model(self):
        """Test risk assessment model creation."""
        risk = RiskAssessment(
            risk_category=RiskCategory.PHYSICAL,
            risk_level=RiskLevel.LOW,
            probability=0.3,
            severity=0.4,
            mitigation_strategies=["Strategy 1", "Strategy 2"]
        )
        
        assert risk.risk_category == RiskCategory.PHYSICAL
        assert risk.probability == 0.3
        assert risk.severity == 0.4
        assert len(risk.mitigation_strategies) == 2
    
    def test_consent_manager_operations(self):
        """Test consent manager CRUD operations."""
        cm = ConsentManager()
        
        # Create consent
        consent = DynamicConsent(
            participant_id="test_cm_001",
            consent_permissions={
                ConsentType.DATA_SHARING: ConsentStatus.ACTIVE,
                ConsentType.RECONTACT: ConsentStatus.ACTIVE
            }
        )
        
        success = cm.create_consent(consent)
        assert success is True
        
        # Retrieve consent
        retrieved = cm.get_consent("test_cm_001")
        assert retrieved is not None
        assert retrieved.participant_id == "test_cm_001"
        assert retrieved.consent_permissions[ConsentType.DATA_SHARING] == ConsentStatus.ACTIVE
        
        # Update consent status
        update_success = cm.update_consent_status(
            "test_cm_001", 
            ConsentType.DATA_SHARING, 
            ConsentStatus.WITHDRAWN
        )
        assert update_success is True
        
        # Verify update
        updated = cm.get_consent("test_cm_001")
        assert updated.consent_permissions[ConsentType.DATA_SHARING] == ConsentStatus.WITHDRAWN
    
    def test_risk_calculator(self):
        """Test risk score calculation."""
        irb_gen = IRBGenerator()
        
        metadata = SessionMetadata(
            session_id="risk_test_001",
            study_name="Risk Test Study",
            principal_investigator="Dr. Test",
            modality=ImagingModality.FMRI,
            session_type=SessionType.TASK_BASED,
            participant_population=ParticipantPopulation.HEALTHY_ADULTS,
            risk_level=RiskLevel.LOW,
            duration_minutes=60,
            expected_participants=20
        )
        
        risk_assessments = [
            RiskAssessment(
                risk_category=RiskCategory.PHYSICAL,
                risk_level=RiskLevel.LOW,
                probability=0.2,
                severity=0.3,
                mitigation_strategies=["Staff monitoring"]
            ),
            RiskAssessment(
                risk_category=RiskCategory.PSYCHOLOGICAL,
                risk_level=RiskLevel.MINIMAL,
                probability=0.1,
                severity=0.2,
                mitigation_strategies=["Counseling available"]
            )
        ]
        
        risk_score = irb_gen.calculate_risk_score(metadata, risk_assessments)
        
        assert "overall_score" in risk_score
        assert "risk_level" in risk_score
        assert "category_scores" in risk_score
        assert risk_score["overall_score"] >= 0
        assert risk_score["overall_score"] <= 1
    
    def test_compliance_checking(self):
        """Test compliance checking functionality."""
        irb_gen = IRBGenerator()
        
        metadata = SessionMetadata(
            session_id="compliance_test_001",
            study_name="Compliance Test Study",
            principal_investigator="Dr. Compliance",
            modality=ImagingModality.EEG,
            session_type=SessionType.RESTING_STATE,
            participant_population=ParticipantPopulation.HEALTHY_ADULTS,
            risk_level=RiskLevel.MINIMAL,
            duration_minutes=30,
            expected_participants=15
        )
        
        # Test with incomplete content
        incomplete_content = "This is an incomplete informed consent form."
        checks = irb_gen.check_compliance(metadata, incomplete_content)
        
        assert len(checks) > 0
        assert any(check.status == ComplianceStatus.NON_COMPLIANT for check in checks)
        
        # Test with complete content
        complete_content = """
        PURPOSE of this study is to investigate brain function.
        PROCEDURE involves EEG recording.
        RISK includes minimal discomfort.
        BENEFIT may contribute to scientific knowledge.
        CONFIDENTIALITY will be maintained.
        VOLUNTARY participation is emphasized.
        CONTACT information: Dr. Compliance
        CONSENT is required before participation.
        """
        
        complete_checks = irb_gen.check_compliance(metadata, complete_content)
        compliant_checks = [check for check in complete_checks if check.status == ComplianceStatus.COMPLIANT]
        assert len(compliant_checks) > 0
    
    def test_new_enum_values(self):
        """Test new enum values are properly defined."""
        # Test ConsentType enum
        assert ConsentType.DATA_SHARING.value == "data_sharing"
        assert ConsentType.RECONTACT.value == "recontact"
        assert ConsentType.FUTURE_RESEARCH.value == "future_research"
        
        # Test ConsentStatus enum
        assert ConsentStatus.ACTIVE.value == "active"
        assert ConsentStatus.WITHDRAWN.value == "withdrawn"
        assert ConsentStatus.PENDING.value == "pending"
        
        # Test RiskCategory enum
        assert RiskCategory.PHYSICAL.value == "physical"
        assert RiskCategory.PSYCHOLOGICAL.value == "psychological"
        assert RiskCategory.PRIVACY.value == "privacy"
        
        # Test ComplianceStatus enum
        assert ComplianceStatus.COMPLIANT.value == "compliant"
        assert ComplianceStatus.NON_COMPLIANT.value == "non_compliant"
        assert ComplianceStatus.NEEDS_REVIEW.value == "needs_review"