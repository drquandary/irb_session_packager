"""
Demonstration of Enhanced IRB Session Packager Features
======================================================

This script demonstrates the new capabilities added to the IRB Session Packager,
showcasing the transformation from a basic paperwork generator to a comprehensive
research lifecycle platform.
"""

from app.models import *
from app.consent_manager import ConsentManager
from app.irb_generator import IRBGenerator
from app.audit_manager import AuditManager
from app.packager import SessionPackager
from datetime import datetime


def demonstrate_enhanced_features():
    """Demonstrate all the new enhanced features."""
    
    print("🧠 IRB Session Packager - Enhanced Features Demo")
    print("=" * 60)
    
    # 1. Dynamic Consent Management
    print("\n1. 📋 Dynamic Consent Management")
    consent_manager = ConsentManager()
    
    # Create dynamic consent
    consent = DynamicConsent(
        participant_id="demo_participant_001",
        consent_permissions={
            ConsentType.DATA_SHARING: ConsentStatus.ACTIVE,
            ConsentType.RECONTACT: ConsentStatus.ACTIVE,
            ConsentType.FUTURE_RESEARCH: ConsentStatus.PENDING,
            ConsentType.GENETIC_ANALYSIS: ConsentStatus.WITHDRAWN
        },
        language_preference="en",
        notes="Demo participant with mixed consent status"
    )
    
    consent_manager.create_consent(consent)
    retrieved = consent_manager.get_consent("demo_participant_001")
    print(f"   ✅ Created consent for participant: {retrieved.participant_id}")
    print(f"   📊 Active permissions: {[p.value for p, s in retrieved.consent_permissions.items() if s == ConsentStatus.ACTIVE]}")
    print(f"   ⚠️  Withdrawn permissions: {[p.value for p, s in retrieved.consent_permissions.items() if s == ConsentStatus.WITHDRAWN]}")
    
    # 2. Interactive Risk Calculator
    print("\n2. ⚖️ Interactive Risk Calculator")
    irb_gen = IRBGenerator()
    
    session_metadata = SessionMetadata(
        session_id="enhanced_demo_001",
        study_name="Enhanced Demo Study",
        principal_investigator="Dr. Enhanced",
        modality=ImagingModality.FMRI,
        session_type=SessionType.TASK_BASED,
        participant_population=ParticipantPopulation.HEALTHY_ADULTS,
        risk_level=RiskLevel.LOW,
        duration_minutes=90,
        expected_participants=100
    )
    
    risk_assessments = [
        RiskAssessment(
            risk_category=RiskCategory.PHYSICAL,
            risk_level=RiskLevel.LOW,
            probability=0.3,
            severity=0.4,
            mitigation_strategies=["MRI safety screening", "Trained technician present"]
        ),
        RiskAssessment(
            risk_category=RiskCategory.PSYCHOLOGICAL,
            risk_level=RiskLevel.MINIMAL,
            probability=0.1,
            severity=0.2,
            mitigation_strategies=["Pre-screening for claustrophobia", "Emergency stop button"]
        ),
        RiskAssessment(
            risk_category=RiskCategory.PRIVACY,
            risk_level=RiskLevel.LOW,
            probability=0.2,
            severity=0.3,
            mitigation_strategies=["Data de-identification", "Secure storage"]
        )
    ]
    
    risk_score = irb_gen.calculate_risk_score(session_metadata, risk_assessments)
    print(f"   🎯 Overall Risk Score: {risk_score['overall_score']:.3f}")
    print(f"   📈 Risk Level: {risk_score['risk_level'].value}")
    print(f"   🔬 Modality Factor: {risk_score['modality_factor']}")
    print(f"   👥 Population Factor: {risk_score['population_factor']}")
    
    # 3. AI-Assisted Compliance Checking
    print("\n3. 🤖 AI-Assisted Compliance Checking")
    
    # Test with incomplete document
    incomplete_doc = "This is an incomplete informed consent form with missing elements."
    compliance_checks = irb_gen.check_compliance(session_metadata, incomplete_doc)
    
    compliant_count = sum(1 for check in compliance_checks if check.status == ComplianceStatus.COMPLIANT)
    non_compliant_count = sum(1 for check in compliance_checks if check.status == ComplianceStatus.NON_COMPLIANT)
    
    print(f"   ✅ Compliant checks: {compliant_count}")
    print(f"   ❌ Non-compliant checks: {non_compliant_count}")
    print(f"   📝 Example issue: {compliance_checks[0].details if compliance_checks else 'None'}")
    
    # 4. Recruitment Planning
    print("\n4. 🎯 Equity-Focused Recruitment Planning")
    
    target_demographics = {
        "age_distribution": {"18-30": 0.4, "31-50": 0.4, "51-65": 0.2},
        "education_level": {"high_school": 0.3, "bachelor": 0.4, "graduate": 0.3},
        "geographic_distribution": {"urban": 0.6, "suburban": 0.3, "rural": 0.1}
    }
    
    recruitment_plan = irb_gen.generate_recruitment_plan(session_metadata, target_demographics)
    print(f"   📊 Target participants: {session_metadata.expected_participants}")
    print(f"   📅 Estimated timeline: {recruitment_plan.estimated_timeline}")
    print(f"   💰 Estimated budget: ${sum(recruitment_plan.budget_considerations.values()):,.0f}")
    print(f"   🌍 Diversity targets: {len(recruitment_plan.diversity_requirements)} categories")
    print(f"   📋 Strategies: {len(recruitment_plan.recruitment_strategies)} planned")
    
    # 5. Audit Trail Management
    print("\n5. 📁 Audit Trail & Version Control")
    audit_manager = AuditManager()
    
    # Log some demo activities
    audit_manager.log_session_package_creation("enhanced_demo_001", "demo_user", session_metadata)
    
    audit_trail = audit_manager.get_audit_trail("enhanced_demo_001")
    print(f"   📝 Audit entries created: {len(audit_trail)}")
    if audit_trail:
        print(f"   🕐 Latest activity: {audit_trail[0].action} by {audit_trail[0].user_id}")
        print(f"   📅 Timestamp: {audit_trail[0].timestamp}")
    
    # 6. Complete Session Package
    print("\n6. 📦 Complete Enhanced Session Package")
    packager = SessionPackager()
    
    package_request = PackageRequest(
        session_metadata=session_metadata,
        include_sop=True,
        include_irb=True,
        include_bids=True
    )
    
    session_package = packager.create_session_package(package_request)
    summary = packager.get_package_summary(session_package)
    
    print(f"   📊 Package Summary:")
    print(f"      - Session ID: {summary['session_id']}")
    print(f"      - Study: {summary['study_name']}")
    print(f"      - IRB Documents: {summary['document_counts']['irb_documents']}")
    print(f"      - SOPs: {summary['document_counts']['sop_documents']}")
    print(f"      - BIDS Events: {summary['document_counts']['bids_events']}")
    print(f"      - Risk Level: {summary['risk_level']}")
    
    print("\n🎉 Enhanced IRB Session Packager Demo Complete!")
    print("   The system now provides comprehensive research lifecycle management")
    print("   from initial consent through final IRB submission and beyond.")
    
    return {
        "consent_created": retrieved.participant_id if retrieved else None,
        "risk_score": risk_score['overall_score'],
        "compliance_checks": len(compliance_checks),
        "recruitment_timeline": recruitment_plan.estimated_timeline,
        "audit_entries": len(audit_trail),
        "package_summary": summary
    }


if __name__ == "__main__":
    results = demonstrate_enhanced_features()
    print(f"\n📈 Demo Results: {results}")