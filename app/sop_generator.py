from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, Template

from .models import ImagingModality, SessionMetadata, SessionType, SOPDocument


class SOPGenerator:
    """Generates Standard Operating Procedures for imaging sessions."""

    def __init__(self, template_dir: Path = None):
        """Initialize SOP generator with template directory."""
        if template_dir is None:
            template_dir = Path(__file__).resolve().parent / "templates" / "sop"

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
        """Create default SOP templates if they don't exist."""
        templates = {
            "fmri_task_sop.md": self._get_fmri_task_template(),
            "eeg_resting_state_sop.md": self._get_eeg_resting_template(),
            "tms_safety_sop.md": self._get_tms_safety_template(),
            "general_setup_sop.md": self._get_general_setup_template(),
            "data_collection_sop.md": self._get_data_collection_template(),
            "quality_control_sop.md": self._get_quality_control_template(),
        }

        for filename, content in templates.items():
            template_path = self.template_dir / filename
            if not template_path.exists():
                template_path.write_text(content)

    def generate_sop(self, session_metadata: SessionMetadata) -> SOPDocument:
        """Generate appropriate SOP based on session metadata."""
        modality = session_metadata.modality
        session_type = session_metadata.session_type

        if modality == ImagingModality.FMRI and session_type == SessionType.TASK_BASED:
            return self._generate_fmri_task_sop(session_metadata)
        elif (
            modality == ImagingModality.EEG
            and session_type == SessionType.RESTING_STATE
        ):
            return self._generate_eeg_resting_sop(session_metadata)
        elif modality == ImagingModality.TMS:
            return self._generate_tms_safety_sop(session_metadata)
        else:
            return self._generate_generic_sop(session_metadata)

    def _generate_fmri_task_sop(self, metadata: SessionMetadata) -> SOPDocument:
        """Generate fMRI task-based SOP."""
        template = self.jinja_env.get_template("fmri_task_sop.md")

        context = {
            "study_name": metadata.study_name,
            "session_id": metadata.session_id,
            "duration": metadata.duration_minutes,
            "pi_name": metadata.principal_investigator,
            "population": metadata.participant_population.value,
        }

        content = template.render(**context)

        return SOPDocument(
            title=f"fMRI Task-Based Protocol - {metadata.study_name}",
            purpose="To establish standardized procedures for conducting task-based fMRI sessions",
            scope="All task-based fMRI sessions in the study",
            procedure_steps=[
                "Pre-scan preparation and safety screening",
                "Participant positioning and head coil setup",
                "Anatomical scan acquisition",
                "Task presentation setup and testing",
                "Functional scan acquisition during task performance",
                "Post-scan procedures and data backup",
            ],
            safety_considerations=[
                "MRI safety screening mandatory for all participants",
                "Emergency procedures review with participant",
                "Continuous monitoring during scan",
                "Immediate response to participant distress signals",
            ],
            equipment_needed=[
                "3T MRI scanner with head coil",
                "Task presentation system",
                "Response collection device",
                "Emergency squeeze ball",
                "Ear protection",
            ],
            quality_control=[
                "Daily phantom scans",
                "Visual inspection of anatomical images",
                "Task timing verification",
                "Motion parameter review",
                "Data backup verification",
            ],
        )

    def _generate_eeg_resting_sop(self, metadata: SessionMetadata) -> SOPDocument:
        """Generate EEG resting-state SOP."""
        return SOPDocument(
            title=f"EEG Resting-State Protocol - {metadata.study_name}",
            purpose="To establish standardized procedures for EEG resting-state data collection",
            scope="All resting-state EEG sessions in the study",
            procedure_steps=[
                "EEG cap preparation and electrode impedance check",
                "Participant seating and comfort adjustment",
                "Resting-state instructions delivery",
                "5-minute eyes-open resting state",
                "5-minute eyes-closed resting state",
                "Data quality check and backup",
            ],
            safety_considerations=[
                "Skin preparation with gentle abrasion",
                "Electrode gel safety check",
                "Participant comfort monitoring",
                "Emergency stop procedures",
            ],
            equipment_needed=[
                "64-channel EEG system",
                "EEG cap with electrodes",
                "Conductive gel",
                "Computer with recording software",
                "Comfortable seating",
            ],
            quality_control=[
                "Impedance check below 5kΩ",
                "Visual inspection of raw data",
                "Artifact detection and marking",
                "Data backup verification",
            ],
        )

    def _generate_tms_safety_sop(self, metadata: SessionMetadata) -> SOPDocument:
        """Generate TMS safety SOP."""
        return SOPDocument(
            title=f"TMS Safety Protocol - {metadata.study_name}",
            purpose="To ensure safe and standardized TMS procedures",
            scope="All TMS sessions in the study",
            procedure_steps=[
                "Pre-session medical screening",
                "Motor threshold determination",
                "Stimulation site localization",
                "Safety parameter verification",
                "Stimulation session execution",
                "Post-session monitoring",
            ],
            safety_considerations=[
                "Contraindication screening",
                "Seizure risk assessment",
                "Hearing protection mandatory",
                "Emergency medical kit available",
            ],
            equipment_needed=[
                "TMS stimulator and coil",
                "Neuronavigation system",
                "EMG recording equipment",
                "Hearing protection",
                "Emergency medical supplies",
            ],
            quality_control=[
                "Equipment calibration verification",
                "Motor threshold confirmation",
                "Stimulation site accuracy check",
                "Adverse event monitoring",
            ],
        )

    def _generate_generic_sop(self, metadata: SessionMetadata) -> SOPDocument:
        """Generate generic SOP for unspecified modalities."""
        return SOPDocument(
            title=f"Research Protocol - {metadata.study_name}",
            purpose=f"To establish standardized procedures for {metadata.modality.value} research sessions",
            scope=f"All {metadata.modality.value} sessions in the study",
            procedure_steps=[
                "Pre-session preparation",
                "Participant setup and safety briefing",
                "Data collection according to protocol",
                "Quality checks during session",
                "Post-session procedures",
                "Data backup and documentation",
            ],
            safety_considerations=[
                "General safety briefing",
                "Emergency contact procedures",
                "Participant rights review",
                "Data privacy protection",
            ],
            equipment_needed=[
                f"{metadata.modality.value} equipment",
                "Safety equipment",
                "Data collection tools",
                "Backup storage",
            ],
            quality_control=[
                "Equipment functionality check",
                "Data quality verification",
                "Documentation review",
                "Backup confirmation",
            ],
        )

    def get_available_templates(self) -> List[str]:
        """Get list of available SOP templates."""
        return [f.name for f in self.template_dir.glob("*.md")]

    def _get_fmri_task_template(self) -> str:
        """Get fMRI task template content."""
        return """# fMRI Task-Based Protocol - {{ study_name }}

## Purpose
To establish standardized procedures for conducting task-based fMRI sessions for {{ study_name }}.

## Scope
All task-based fMRI sessions conducted as part of {{ study_name }}.

## Pre-Session Checklist
- [ ] MRI safety screening completed
- [ ] Task presentation system tested
- [ ] Response device calibrated
- [ ] Emergency procedures reviewed

## Procedure Steps

### 1. Pre-scan Preparation (10 minutes)
- Complete MRI safety screening form
- Remove all metallic objects
- Change into MRI-safe clothing
- Review task instructions

### 2. Participant Positioning (5 minutes)
- Position participant in head coil
- Secure head with padding
- Provide emergency squeeze ball
- Test intercom communication

### 3. Anatomical Scan (5 minutes)
- Acquire localizer images
- Run T1-weighted anatomical scan
- Verify image quality

### 4. Task Setup (5 minutes)
- Load task presentation program
- Verify stimulus timing
- Test response collection
- Confirm task parameters

### 5. Functional Scan ({{ duration }} minutes)
- Begin task-based fMRI acquisition
- Monitor participant comfort
- Check for motion artifacts
- Record any issues

### 6. Post-Scan (5 minutes)
- Check participant well-being
- Backup scan data
- Complete session documentation

## Safety Considerations
- MRI safety screening mandatory
- Emergency procedures review required
- Continuous monitoring during scan
- Immediate response to distress signals

## Equipment Needed
- 3T MRI scanner with head coil
- Task presentation system
- Response collection device
- Emergency squeeze ball
- Ear protection

## Quality Control
- Daily phantom scans
- Visual inspection of anatomical images
- Task timing verification
- Motion parameter review
- Data backup verification
"""

    def _get_eeg_resting_template(self) -> str:
        """Get EEG resting-state template content."""
        return """# EEG Resting-State Protocol - {{ study_name }}

## Purpose
To establish standardized procedures for EEG resting-state data collection.

## Scope
All resting-state EEG sessions conducted as part of {{ study_name }}.

## Pre-Session Checklist
- [ ] EEG equipment calibrated
- [ ] Electrodes impedance checked
- [ ] Recording software configured
- [ ] Participant comfort assessed

## Procedure Steps

### 1. EEG Setup (15 minutes)
- Prepare EEG cap with electrodes
- Check electrode impedances (<5kΩ)
- Configure recording parameters
- Test data acquisition

### 2. Participant Preparation (5 minutes)
- Seat participant comfortably
- Explain resting-state instructions
- Position electrodes carefully
- Verify comfort level

### 3. Resting-State Recording (10 minutes)
- Begin eyes-open resting state (5 min)
- Provide instructions for eyes-open condition
- Begin eyes-closed resting state (5 min)
- Monitor data quality throughout

### 4. Data Quality Check (5 minutes)
- Review impedance levels
- Check for artifacts
- Verify data integrity
- Backup recording files

## Safety Considerations
- Gentle skin preparation
- Electrode gel safety check
- Participant comfort monitoring
- Emergency stop procedures

## Equipment Needed
- 64-channel EEG system
- EEG cap with electrodes
- Conductive gel
- Recording software
- Comfortable seating

## Quality Control
- Impedance check below 5kΩ
- Visual inspection of raw data
- Artifact detection and marking
- Data backup verification
"""

    def _get_tms_safety_template(self) -> str:
        """Get TMS safety template content."""
        return """# TMS Safety Protocol - {{ study_name }}

## Purpose
To ensure safe and standardized TMS procedures for {{ study_name }}.

## Scope
All TMS sessions conducted as part of {{ study_name }}.

## Pre-Session Checklist
- [ ] Medical screening completed
- [ ] Contraindications reviewed
- [ ] Equipment calibration verified
- [ ] Emergency medical kit available

## Procedure Steps

### 1. Pre-session Medical Screening (10 minutes)
- Review medical history
- Check contraindications
- Assess seizure risk
- Obtain informed consent

### 2. Motor Threshold Determination (15 minutes)
- Position TMS coil appropriately
- Identify motor hotspot
- Determine resting motor threshold
- Document threshold value

### 3. Stimulation Site Localization (10 minutes)
- Use neuronavigation system
- Mark stimulation site
- Verify accuracy
- Record coordinates

### 4. Safety Parameter Verification (5 minutes)
- Confirm stimulation parameters
- Check safety limits
- Verify emergency procedures
- Test stop mechanisms

### 5. Stimulation Session ({{ duration }} minutes)
- Begin stimulation protocol
- Monitor participant closely
- Watch for adverse effects
- Document any issues

### 6. Post-session Monitoring (15 minutes)
- Monitor for adverse events
- Check participant well-being
- Document session outcome
- Schedule follow-up if needed

## Safety Considerations
- Contraindication screening mandatory
- Seizure risk assessment required
- Hearing protection mandatory
- Emergency medical kit available

## Equipment Needed
- TMS stimulator and coil
- Neuronavigation system
- EMG recording equipment
- Hearing protection
- Emergency medical supplies

## Quality Control
- Equipment calibration verification
- Motor threshold confirmation
- Stimulation site accuracy check
- Adverse event monitoring
"""

    def _get_general_setup_template(self) -> str:
        """Get general setup template content."""
        return """# General Research Setup Protocol

## Purpose
To establish standardized setup procedures for research sessions.

## Scope
All research sessions requiring general setup procedures.

## Setup Checklist
- [ ] Equipment inventory completed
- [ ] Safety checks performed
- [ ] Environment prepared
- [ ] Documentation ready

## Procedure Steps
1. Equipment preparation and testing
2. Environment setup and safety check
3. Participant area preparation
4. Documentation review
5. Final safety verification
"""

    def _get_data_collection_template(self) -> str:
        """Get data collection template content."""
        return """# Data Collection Protocol

## Purpose
To establish standardized data collection procedures.

## Scope
All research data collection activities.

## Collection Checklist
- [ ] Data collection plan reviewed
- [ ] Equipment tested and calibrated
- [ ] Quality control measures in place
- [ ] Backup procedures confirmed

## Procedure Steps
1. Pre-collection equipment check
2. Data collection according to protocol
3. Real-time quality monitoring
4. Data backup and verification
5. Post-collection documentation
"""

    def _get_quality_control_template(self) -> str:
        """Get quality control template content."""
        return """# Quality Control Protocol

## Purpose
To ensure data quality and protocol compliance.

## Scope
All quality control activities in research sessions.

## QC Checklist
- [ ] Quality standards defined
- [ ] Monitoring procedures established
- [ ] Documentation requirements set
- [ ] Review schedule confirmed

## Procedure Steps
1. Define quality metrics
2. Implement monitoring procedures
3. Conduct regular quality checks
4. Document findings and actions
5. Continuous improvement review
"""
