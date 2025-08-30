from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from .models import (
    ImagingModality,
    IRBDocument,
    ParticipantPopulation,
    RiskLevel,
    SessionMetadata,
)


class IRBGenerator:
    """Generates IRB-compliant documents and appendices."""

    def __init__(self, template_dir: Path = None):
        """Initialize IRB generator with template directory."""
        if template_dir is None:
            template_dir = Path(__file__).resolve().parent / "templates" / "irb"

        self.template_dir = template_dir
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Create default templates if they don't exist
        self._create_default_templates()

    def _create_default_templates(self):
        """Create default IRB templates if they don't exist."""
        templates = {
            "informed_consent.md": self._get_informed_consent_template(),
            "risk_assessment.md": self._get_risk_assessment_template(),
            "protocol_summary.md": self._get_protocol_summary_template(),
            "data_management.md": self._get_data_management_template(),
            "adverse_events.md": self._get_adverse_events_template(),
            "recruitment.md": self._get_recruitment_template(),
        }

        for filename, content in templates.items():
            template_path = self.template_dir / filename
            if not template_path.exists():
                template_path.write_text(content)

    def generate_irb_package(
        self, session_metadata: SessionMetadata
    ) -> List[IRBDocument]:
        """Generate complete IRB document package."""
        documents = []

        # Generate informed consent
        documents.append(self._generate_informed_consent(session_metadata))

        # Generate risk assessment
        documents.append(self._generate_risk_assessment(session_metadata))

        # Generate protocol summary
        documents.append(self._generate_protocol_summary(session_metadata))

        # Generate data management plan
        documents.append(self._generate_data_management_plan(session_metadata))

        # Generate adverse events protocol
        documents.append(self._generate_adverse_events_protocol(session_metadata))

        # Generate recruitment materials
        documents.append(self._generate_recruitment_materials(session_metadata))

        return documents

    def _generate_informed_consent(self, metadata: SessionMetadata) -> IRBDocument:
        """Generate informed consent document."""
        risk_level = metadata.risk_level

        if risk_level == RiskLevel.MINIMAL:
            risk_description = "This study involves minimal risk, which means the probability and magnitude of harm or discomfort anticipated in the research are not greater than those ordinarily encountered in daily life."
        elif risk_level == RiskLevel.LOW:
            risk_description = "This study involves low risk, with potential for minor discomfort or inconvenience that is temporary and reversible."
        elif risk_level == RiskLevel.MODERATE:
            risk_description = "This study involves moderate risk, with potential for temporary discomfort or mild adverse effects."
        else:
            risk_description = "This study involves higher risk, with potential for significant discomfort or adverse effects that will be closely monitored."

        content = f"""
# INFORMED CONSENT FORM
## {metadata.study_name}

### Principal Investigator: {metadata.principal_investigator}
### Study ID: {metadata.session_id}
### Date: {datetime.now().strftime('%B %d, %Y')}

---

## PURPOSE OF STUDY
You are being asked to participate in a research study. The purpose of this study is to investigate brain function using {metadata.modality.value} imaging techniques.

## STUDY PROCEDURES
If you agree to participate, you will undergo the following procedures:
- Duration: Approximately {metadata.duration_minutes} minutes
- Modality: {metadata.modality.value}
- Session type: {metadata.session_type.value.replace('_', ' ').title()}
- Participant population: {metadata.participant_population.value.replace('_', ' ').title()}

## RISKS AND DISCOMFORTS
{risk_description}

Specific risks associated with {metadata.modality.value} include:
{self._get_modality_specific_risks(metadata.modality)}

## BENEFITS
There may be no direct benefit to you from participating in this study. However, your participation may contribute to scientific knowledge about brain function and may benefit future patients with neurological or psychiatric conditions.

## CONFIDENTIALITY
Your identity will be kept confidential. All data will be coded with a study ID number, and your name will not appear in any reports or publications. Data will be stored securely and access will be limited to authorized study personnel.

## VOLUNTARY PARTICIPATION
Your participation in this study is voluntary. You may choose not to participate or may withdraw from the study at any time without penalty or loss of benefits to which you are otherwise entitled.

## CONTACT INFORMATION
If you have questions about this study, please contact:
- Principal Investigator: {metadata.principal_investigator}
- IRB Contact: [Institutional Review Board contact information]

## CONSENT
I have read and understand the information provided above. I voluntarily agree to participate in this study.

Participant Signature: _________________ Date: _________
Researcher Signature: _________________ Date: _________
"""

        return IRBDocument(
            document_type="informed_consent", content=content.strip(), version="1.0"
        )

    def _generate_risk_assessment(self, metadata: SessionMetadata) -> IRBDocument:
        """Generate risk assessment document."""
        risk_factors = self._get_risk_factors(metadata)

        content = f"""
# RISK ASSESSMENT FORM
## {metadata.study_name}

### Study Information
- **Study ID**: {metadata.session_id}
- **Principal Investigator**: {metadata.principal_investigator}
- **Modality**: {metadata.modality.value}
- **Population**: {metadata.participant_population.value.replace('_', ' ').title()}
- **Risk Level**: {metadata.risk_level.value.title()}

### Risk Assessment Summary

#### Participant Population Risks
{self._get_population_risks(metadata.participant_population)}

#### Modality-Specific Risks
{self._get_modality_risks(metadata.modality)}

#### Risk Mitigation Strategies
{self._get_risk_mitigation_strategies(metadata)}

#### Risk-Benefit Analysis
The potential benefits of this research outweigh the identified risks due to:
- Comprehensive safety protocols in place
- Experienced research team
- Continuous monitoring procedures
- Immediate response capabilities for adverse events

### IRB Determination
Based on the above assessment, this study is classified as {metadata.risk_level.value} risk.

Date: {datetime.now().strftime('%B %d, %Y')}
Reviewed by: _________________
"""

        return IRBDocument(
            document_type="risk_assessment", content=content.strip(), version="1.0"
        )

    def _generate_protocol_summary(self, metadata: SessionMetadata) -> IRBDocument:
        """Generate protocol summary document."""
        content = f"""
# PROTOCOL SUMMARY
## {metadata.study_name}

### Study Overview
This study aims to investigate brain function using {metadata.modality.value} imaging in {metadata.participant_population.value.replace('_', ' ')} participants.

### Objectives
1. Primary: To characterize brain activity patterns during {metadata.session_type.value.replace('_', ' ')} states
2. Secondary: To establish normative data for {metadata.modality.value} measures
3. Exploratory: To identify potential biomarkers for future clinical applications

### Study Design
- **Type**: Observational neuroimaging study
- **Duration**: Single session, {metadata.duration_minutes} minutes
- **Participants**: {metadata.expected_participants} {metadata.participant_population.value.replace('_', ' ')} participants
- **Setting**: Research imaging facility

### Procedures
1. Informed consent process
2. Safety screening and eligibility confirmation
3. {metadata.modality.value} data acquisition ({metadata.duration_minutes} minutes)
4. Data quality assessment
5. Participant debriefing

### Data Collection
- {metadata.modality.value} raw data acquisition
- Demographic and clinical questionnaires
- Safety monitoring throughout

### Data Analysis
- Preprocessing and quality control
- Statistical analysis of brain activity patterns
- Comparison with existing normative databases
- Reporting of findings

### Timeline
- Study duration: 12 months
- Participant recruitment: 6 months
- Data collection: 3 months
- Analysis and reporting: 3 months

### Personnel
- Principal Investigator: {metadata.principal_investigator}
- Research team: Trained imaging technicians and research coordinators
"""

        return IRBDocument(
            document_type="protocol_summary", content=content.strip(), version="1.0"
        )

    def _generate_data_management_plan(self, metadata: SessionMetadata) -> IRBDocument:
        """Generate data management plan."""
        content = f"""
# DATA MANAGEMENT PLAN
## {metadata.study_name}

### Data Collection
- **Primary Data**: {metadata.modality.value} imaging data
- **Secondary Data**: Demographics, clinical assessments
- **Format**: BIDS-compliant neuroimaging format
- **Quality Control**: Automated and manual QC procedures

### Data Storage
- **Location**: Secure research server with encrypted storage
- **Backup**: Multiple redundant backups with off-site storage
- **Access**: Role-based access control with audit logging
- **Retention**: Minimum 7 years per institutional policy

### Data Security
- **Encryption**: AES-256 encryption for data at rest and in transit
- **Access Control**: Unique user accounts with strong passwords
- **Audit Trail**: Complete logging of all data access and modifications
- **Physical Security**: Secure server room with restricted access

### Data Sharing
- **De-identification**: All data will be de-identified before sharing
- **Sharing Agreements**: Data Use Agreements for external collaborators
- **Public Repository**: De-identified data may be shared in public repositories
- **Timeline**: Data sharing after primary publication

### Privacy Protection
- **HIPAA Compliance**: Full compliance with HIPAA regulations
- **De-identification**: Removal of all identifying information
- **Limited Access**: Access restricted to authorized research personnel
- **Training**: All personnel complete privacy and security training

### Data Destruction
- **Timeline**: Data destruction 7 years after study completion
- **Method**: Secure deletion with verification
- **Documentation**: Certificate of destruction for audit purposes
"""

        return IRBDocument(
            document_type="data_management", content=content.strip(), version="1.0"
        )

    def _generate_adverse_events_protocol(
        self, metadata: SessionMetadata
    ) -> IRBDocument:
        """Generate adverse events protocol."""
        content = f"""
# ADVERSE EVENTS PROTOCOL
## {metadata.study_name}

### Definition of Adverse Events
Adverse events are any untoward medical occurrences in study participants, including:
- Physical symptoms or injuries
- Psychological distress
- Technical malfunctions causing harm
- Privacy breaches

### Reporting Requirements
- **Immediate**: Life-threatening events within 24 hours
- **Expedited**: Serious adverse events within 72 hours
- **Routine**: All other adverse events within 7 days

### Contact Information
- **Principal Investigator**: {metadata.principal_investigator}
- **IRB Contact**: [Institutional Review Board]
- **Emergency**: 911 or local emergency services

### Procedures for Adverse Events

#### 1. Immediate Response
- Ensure participant safety and well-being
- Provide appropriate medical care
- Document incident details
- Notify principal investigator immediately

#### 2. Assessment
- Evaluate severity and causality
- Determine relationship to study procedures
- Assess impact on participant safety
- Review protocol modifications if needed

#### 3. Reporting
- Complete adverse event report form
- Submit to IRB within required timeframes
- Update consent forms if necessary
- Implement corrective actions

#### 4. Follow-up
- Monitor participant until resolution
- Provide additional care as needed
- Document outcome and lessons learned
- Update study procedures if required

### Risk Mitigation
- Comprehensive safety protocols
- Trained research personnel
- Emergency response procedures
- Regular safety monitoring

### Documentation
- Adverse event log maintained
- Regular safety reports to IRB
- Annual continuing review
- Final safety summary report
"""

        return IRBDocument(
            document_type="adverse_events", content=content.strip(), version="1.0"
        )

    def _generate_recruitment_materials(self, metadata: SessionMetadata) -> IRBDocument:
        """Generate recruitment materials."""
        population_desc = self._get_population_description(
            metadata.participant_population
        )

        content = f"""
# RECRUITMENT MATERIALS
## {metadata.study_name}

### Recruitment Flyer

#### Study Title: {metadata.study_name}

#### We are looking for:
{population_desc}

#### What is involved?
- Single research session lasting {metadata.duration_minutes} minutes
- {metadata.modality.value} brain imaging
- Questionnaires and assessments
- Compensation for time and travel

#### Who can participate?
- {self._get_inclusion_criteria(metadata.participant_population)}
- Generally healthy adults
- No contraindications for {metadata.modality.value}

#### Contact Information:
- Principal Investigator: {metadata.principal_investigator}
- Email: [study email]
- Phone: [study phone number]

### Recruitment Email Template

Subject: Participate in Brain Imaging Research Study

Dear [Name],

We are conducting a research study investigating brain function using {metadata.modality.value} imaging. We are looking for {population_desc} to participate in a single research session lasting {metadata.duration_minutes} minutes.

If you are interested in learning more about this study, please contact us at [contact information].

Thank you for your consideration.

Best regards,
{metadata.principal_investigator}

### Social Media Recruitment
"Researchers at [institution] are looking for {population_desc} to participate in a brain imaging study. Compensation provided. Contact [email] for details."

### Inclusion Criteria
{self._get_detailed_inclusion_criteria(metadata)}

### Exclusion Criteria
{self._get_exclusion_criteria(metadata)}
"""

        return IRBDocument(
            document_type="recruitment", content=content.strip(), version="1.0"
        )

    def _get_modality_specific_risks(self, modality: ImagingModality) -> str:
        """Get modality-specific risk descriptions."""
        risks = {
            ImagingModality.FMRI: """
- Claustrophobia or anxiety in scanner
- Loud noise exposure (hearing protection provided)
- Potential for metallic object injuries
- Discomfort from lying still
""",
            ImagingModality.EEG: """
- Skin irritation from electrodes
- Discomfort from electrode gel
- Mild headache from prolonged wearing
- Rare allergic reaction to electrode materials
""",
            ImagingModality.TMS: """
- Headache or scalp discomfort
- Rare seizure risk (less than 0.1%)
- Hearing protection required
- Muscle twitching during stimulation
""",
            ImagingModality.MRI: """
- Claustrophobia or anxiety
- Metallic object safety concerns
- Gadolinium contrast risks (if applicable)
- Loud noise exposure
""",
            ImagingModality.PET: """
- Radiation exposure (minimal)
- Discomfort from IV injection
- Rare allergic reaction to tracer
- Need to remain still for extended period
""",
            ImagingModality.MEG: """
- Minimal physical risks
- Discomfort from prolonged sitting
- Metallic object interference
- Need for quiet environment
""",
        }
        return risks.get(
            modality,
            "- Minimal physical risks\n- Discomfort from procedures\n- Rare complications",
        )

    def _get_risk_factors(self, metadata: SessionMetadata) -> List[str]:
        """Get risk factors for assessment."""
        factors = []

        # Population-based risks
        if metadata.participant_population == ParticipantPopulation.CHILDREN:
            factors.append("Vulnerable population - enhanced protections required")
        elif metadata.participant_population == ParticipantPopulation.ELDERLY:
            factors.append("Age-related health considerations")
        elif metadata.participant_population == ParticipantPopulation.CLINICAL:
            factors.append("Clinical population - potential for exacerbation")

        # Modality-based risks
        if metadata.modality == ImagingModality.TMS:
            factors.append("Seizure risk with brain stimulation")
        elif metadata.modality == ImagingModality.FMRI:
            factors.append("Claustrophobia and noise exposure")

        return factors

    def _get_population_risks(self, population: ParticipantPopulation) -> str:
        """Get population-specific risk descriptions."""
        risks = {
            ParticipantPopulation.HEALTHY_ADULTS: "Healthy adult population with standard risk profile.",
            ParticipantPopulation.CLINICAL: "Clinical population requires enhanced monitoring for potential symptom exacerbation.",
            ParticipantPopulation.CHILDREN: "Pediatric population requires enhanced protections and parental consent.",
            ParticipantPopulation.ELDERLY: "Elderly population may have age-related health considerations and comorbidities.",
            ParticipantPopulation.PREGNANT: "Pregnant population requires additional safety considerations for fetal protection.",
        }
        return risks.get(population, "Standard population risk profile.")

    def _get_modality_risks(self, modality: ImagingModality) -> str:
        """Get modality-specific risk assessment."""
        risks = {
            ImagingModality.FMRI: "MRI risks include claustrophobia, noise exposure, and metallic object safety concerns.",
            ImagingModality.EEG: "EEG risks are minimal, primarily involving skin irritation and discomfort.",
            ImagingModality.TMS: "TMS risks include headache, scalp discomfort, and rare seizure risk.",
            ImagingModality.MRI: "MRI risks include claustrophobia, noise, and metallic object safety.",
            ImagingModality.PET: "PET risks include radiation exposure and IV injection discomfort.",
            ImagingModality.MEG: "MEG risks are minimal, primarily involving discomfort from prolonged sitting.",
        }
        return risks.get(modality, "Standard procedural risks.")

    def _get_risk_mitigation_strategies(self, metadata: SessionMetadata) -> str:
        """Get risk mitigation strategies."""
        strategies = []

        # General strategies
        strategies.extend(
            [
                "Comprehensive informed consent process",
                "Medical screening and eligibility assessment",
                "Trained research personnel",
                "Emergency response procedures",
                "Continuous monitoring during procedures",
            ]
        )

        # Modality-specific strategies
        if metadata.modality == ImagingModality.TMS:
            strategies.extend(
                [
                    "Seizure risk screening",
                    "Motor threshold determination",
                    "Safety parameter limits",
                    "Emergency medical kit",
                ]
            )
        elif metadata.modality in [ImagingModality.FMRI, ImagingModality.MRI]:
            strategies.extend(
                [
                    "MRI safety screening",
                    "Hearing protection",
                    "Emergency communication",
                    "Claustrophobia assessment",
                ]
            )

        return "\n".join(f"- {strategy}" for strategy in strategies)

    def _get_population_description(self, population: ParticipantPopulation) -> str:
        """Get population description for recruitment."""
        descriptions = {
            ParticipantPopulation.HEALTHY_ADULTS: "healthy adults aged 18-65",
            ParticipantPopulation.CLINICAL: "individuals with [specific condition]",
            ParticipantPopulation.CHILDREN: "children aged 8-17",
            ParticipantPopulation.ELDERLY: "adults aged 65 and older",
            ParticipantPopulation.PREGNANT: "pregnant women in their second or third trimester",
        }
        return descriptions.get(population, "adults")

    def _get_inclusion_criteria(self, population: ParticipantPopulation) -> str:
        """Get inclusion criteria for recruitment."""
        criteria = {
            ParticipantPopulation.HEALTHY_ADULTS: "Ages 18-65, generally healthy",
            ParticipantPopulation.CLINICAL: "Diagnosed with [condition], stable on medication",
            ParticipantPopulation.CHILDREN: "Ages 8-17, parental consent required",
            ParticipantPopulation.ELDERLY: "Ages 65+, community-dwelling",
            ParticipantPopulation.PREGNANT: "Pregnant women, 2nd or 3rd trimester",
        }
        return criteria.get(population, "Generally healthy adults")

    def _get_detailed_inclusion_criteria(self, metadata: SessionMetadata) -> str:
        """Get detailed inclusion criteria."""
        base_criteria = [
            f"Ages appropriate for {metadata.participant_population.value.replace('_', ' ')} population",
            "Able to provide informed consent (or parental consent)",
            "Able to comply with study procedures",
            "No contraindications for study procedures",
        ]

        # Add modality-specific criteria
        if metadata.modality == ImagingModality.TMS:
            base_criteria.extend(
                [
                    "No history of seizures or epilepsy",
                    "No implanted medical devices",
                    "No current pregnancy",
                ]
            )
        elif metadata.modality in [ImagingModality.FMRI, ImagingModality.MRI]:
            base_criteria.extend(
                [
                    "No MRI contraindications (metal implants, claustrophobia)",
                    "Able to lie still for extended periods",
                ]
            )

        return "\n".join(f"- {criterion}" for criterion in base_criteria)

    def _get_exclusion_criteria(self, metadata: SessionMetadata) -> str:
        """Get exclusion criteria."""
        criteria = [
            "Unable to provide informed consent",
            "Contraindications for study procedures",
            "Current substance abuse",
            "Severe psychiatric symptoms",
        ]

        # Add modality-specific exclusions
        if metadata.modality == ImagingModality.TMS:
            criteria.extend(
                [
                    "History of seizures or epilepsy",
                    "Implanted medical devices",
                    "Current pregnancy",
                ]
            )
        elif metadata.modality in [ImagingModality.FMRI, ImagingModality.MRI]:
            criteria.extend(
                [
                    "MRI contraindications (metal implants)",
                    "Severe claustrophobia",
                    "Unable to lie still",
                ]
            )

        return "\n".join(f"- {criterion}" for criterion in criteria)

    def _get_informed_consent_template(self):
        """Get default informed consent template."""
        return """
# INFORMED CONSENT FORM
## {{ study_name }}

### Principal Investigator: {{ principal_investigator }}
### Study ID: {{ session_id }}
### Date: {{ date }}

---

## PURPOSE OF STUDY
You are being asked to participate in a research study involving {{ modality }} imaging techniques.

## STUDY PROCEDURES
- Duration: Approximately {{ duration_minutes }} minutes
- Session type: {{ session_type }}
- Participant population: {{ participant_population }}

## RISKS AND DISCOMFORTS
{{ risk_description }}

## BENEFITS
There are no direct benefits to participants, but findings may contribute to scientific knowledge.

## CONFIDENTIALITY
All data will be de-identified and stored securely according to institutional policies.

## VOLUNTARY PARTICIPATION
Participation is voluntary and you may withdraw at any time without penalty.

---
Participant Signature: ___________________ Date: _________
"""

    def _get_risk_assessment_template(self):
        """Get default risk assessment template."""
        return """
# RISK ASSESSMENT
## {{ study_name }}

### Risk Level: {{ risk_level }}

### Potential Risks:
- Physical discomfort during imaging procedures
- Psychological distress from experimental tasks
- Privacy risks from data collection

### Risk Mitigation:
- Trained personnel monitoring all procedures
- Emergency protocols in place
- Secure data handling procedures
- Right to withdraw at any time

### Benefit-Risk Analysis:
Scientific benefits outweigh minimal risks to participants.
"""

    def _get_protocol_summary_template(self):
        """Get default protocol summary template."""
        return """
# PROTOCOL SUMMARY
## {{ study_name }}

### Study Overview:
{{ study_description }}

### Objectives:
- Primary: {{ primary_objective }}
- Secondary: {{ secondary_objectives }}

### Study Design:
- Type: {{ study_type }}
- Duration: {{ duration_minutes }} minutes
- Sample Size: {{ target_enrollment }}

### Procedures:
{{ procedures }}

### Data Collection:
{{ data_collection }}
"""

    def _get_data_management_template(self):
        """Get default data management template."""
        return """
# DATA MANAGEMENT PLAN
## {{ study_name }}

### Data Collection:
- Type: {{ data_types }}
- Format: BIDS-compliant neuroimaging data
- Storage: Secure institutional servers

### Privacy Protection:
- De-identification procedures
- Access controls and encryption
- HIPAA compliance

### Data Retention:
- Duration: 7 years minimum
- Destruction timeline per institutional policy

### Data Sharing:
- De-identified data sharing after publication
- Public repository deposits as appropriate
"""

    def _get_adverse_events_template(self):
        """Get default adverse events template."""
        return """
# ADVERSE EVENTS PROTOCOL
## {{ study_name }}

### Definitions:
Adverse events include any untoward medical occurrences during study participation.

### Reporting Timeline:
- Immediate: Life-threatening events (24 hours)
- Expedited: Serious adverse events (72 hours)
- Routine: All other events (7 days)

### Contact Information:
- Principal Investigator: {{ principal_investigator }}
- IRB Office: {{ irb_contact }}
- Emergency: 911

### Documentation:
All adverse events will be documented and reported per institutional requirements.
"""

    def _get_recruitment_template(self):
        """Get default recruitment template."""
        return """
# RECRUITMENT MATERIALS
## {{ study_name }}

### Study Advertisement:

**VOLUNTEERS NEEDED FOR BRAIN IMAGING STUDY**

We are looking for healthy volunteers to participate in a research study using {{ modality }} to understand brain function.

**What's Involved:**
- Single {{ duration_minutes }}-minute session
- Compensation provided
- Contributes to important scientific research

**Who Can Participate:**
{{ inclusion_criteria }}

**Who Cannot Participate:**
{{ exclusion_criteria }}

**Contact Information:**
Email: {{ contact_email }}
Phone: {{ contact_phone }}

This study has been approved by the Institutional Review Board.
"""
