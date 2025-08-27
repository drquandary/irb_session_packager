# IRB Session Packager

A comprehensive FastAPI-based web application for creating standard operating procedures, IRB appendices, and BIDS event templates for imaging research sessions.

## Features

### 🏥 IRB Compliance
- **Informed Consent Forms**: Auto-generated consent documents tailored to study parameters
- **Risk Assessment**: Comprehensive risk evaluation based on modality and population
- **Protocol Summaries**: IRB-compliant study protocol documentation
- **Data Management Plans**: HIPAA-compliant data handling procedures
- **Adverse Events Protocol**: Safety monitoring and reporting procedures
- **Recruitment Materials**: IRB-approved recruitment flyers and communications

### 📋 Standard Operating Procedures
- **Modality-Specific SOPs**: Customized protocols for fMRI, EEG, TMS, MRI, PET, MEG
- **Task-Based Protocols**: Detailed procedures for task-based imaging sessions
- **Resting-State Protocols**: Standardized resting-state data collection procedures
- **Safety Protocols**: Comprehensive safety guidelines and emergency procedures
- **Quality Control**: Standardized QC measures and validation procedures

### 📊 BIDS Compliance
- **Event Templates**: BIDS-compliant event files for all major imaging modalities
- **Dataset Structure**: Complete BIDS directory structure and metadata
- **Task JSON**: BIDS task configuration files
- **Participants Template**: Standardized participant metadata
- **README & CHANGES**: BIDS-compliant documentation

### 📦 Session Packaging
- **Multiple Export Formats**: JSON, PDF, DOCX, BIDS, ZIP
- **Validation Engine**: Comprehensive package validation
- **Summary Reports**: Package overview and statistics
- **Custom Events**: Support for custom BIDS events

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload
```

### Basic Usage

#### 1. Create a Session Package

```bash
curl -X POST http://localhost:8000/api/create-package \
  -H "Content-Type: application/json" \
  -d '{
    "session_metadata": {
      "session_id": "study_001_session_01",
      "study_name": "Cognitive Neuroimaging Study",
      "principal_investigator": "Dr. Jane Smith",
      "modality": "fMRI",
      "session_type": "task_based",
      "participant_population": "healthy_adults",
      "risk_level": "minimal",
      "duration_minutes": 90,
      "expected_participants": 100
    },
    "include_sop": true,
    "include_irb": true,
    "include_bids": true
  }'
```

#### 2. Get Package Summary

```bash
curl http://localhost:8000/api/package-summary/study_001_session_01
```

#### 3. Export Package

```bash
curl -X POST http://localhost:8000/api/export-package \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "study_001_session_01",
    "formats": ["pdf", "docx", "bids", "zip"]
  }'
```

#### 4. Download Package

```bash
curl http://localhost:8000/api/download-package/study_001_session_01?format=zip
```

## API Endpoints

### Core Endpoints

- `GET /api/health` - Health check
- `GET /api/modalities` - Available modalities and options
- `POST /api/create-package` - Create new session package
- `POST /api/export-package` - Export package in various formats
- `GET /api/download-package/{session_id}` - Download package
- `GET /api/package-summary/{session_id}` - Get package summary
- `POST /api/validate-package` - Validate package before creation

## Supported Modalities

### Imaging Modalities
- **fMRI** - Functional Magnetic Resonance Imaging
- **EEG** - Electroencephalography
- **TMS** - Transcranial Magnetic Stimulation
- **MRI** - Magnetic Resonance Imaging
- **PET** - Positron Emission Tomography
- **MEG** - Magnetoencephalography

### Session Types
- **task_based** - Task-based functional imaging
- **resting_state** - Resting-state connectivity
- **stimulation** - Stimulation paradigms
- **clinical** - Clinical assessment protocols
- **pilot** - Pilot/feasibility studies

### Participant Populations
- **healthy_adults** - Healthy adult volunteers
- **clinical_population** - Clinical populations
- **children** - Pediatric participants
- **elderly** - Older adult populations
- **pregnant** - Pregnant participants

### Risk Levels
- **minimal** - Minimal risk research
- **low** - Low risk procedures
- **moderate** - Moderate risk procedures
- **high** - High risk procedures

## Package Structure

Each session package includes:

### 1. Standard Operating Procedures
- **Title**: Descriptive protocol title
- **Purpose**: Clear statement of protocol purpose
- **Scope**: Applicability and limitations
- **Procedure Steps**: Step-by-step instructions
- **Safety Considerations**: Risk mitigation strategies
- **Equipment Needed**: Required materials and tools
- **Quality Control**: Validation and QC measures

### 2. IRB Documents
- **Informed Consent**: Participant consent forms
- **Risk Assessment**: Comprehensive risk evaluation
- **Protocol Summary**: IRB protocol documentation
- **Data Management Plan**: Data handling procedures
- **Adverse Events Protocol**: Safety monitoring
- **Recruitment Materials**: IRB-approved recruitment

### 3. BIDS Templates
- **Dataset Description**: BIDS dataset metadata
- **Participants Template**: Participant demographics
- **Event Files**: BIDS-compliant event timing
- **Task Configuration**: Task-specific parameters
- **Documentation**: README and CHANGES files

## Configuration

### Environment Variables
```bash
# Optional: Custom template directories
SOP_TEMPLATE_DIR=/custom/sop/templates
IRB_TEMPLATE_DIR=/custom/irb/templates
BIDS_TEMPLATE_DIR=/custom/bids/templates
```

### Custom Templates
Place custom templates in:
- `app/templates/sop/` - SOP templates
- `app/templates/irb/` - IRB document templates
- `app/templates/bids/` - BIDS templates

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=app tests/
```

### Adding New Modalities
1. Add new enum value in `app/models.py`
2. Update SOP generator in `app/sop_generator.py`
3. Add corresponding templates in `app/templates/`
4. Update tests

### Customizing Templates
1. Create template directory structure
2. Add custom templates following naming conventions
3. Update configuration if needed

## Examples

### Example 1: fMRI Task-Based Study
```json
{
  "session_metadata": {
    "session_id": "fmri_stroop_001",
    "study_name": "Stroop Task fMRI Study",
    "principal_investigator": "Dr. Alice Johnson",
    "modality": "fMRI",
    "session_type": "task_based",
    "participant_population": "healthy_adults",
    "risk_level": "minimal",
    "duration_minutes": 75,
    "expected_participants": 50
  }
}
```

### Example 2: EEG Resting-State Study
```json
{
  "session_metadata": {
    "session_id": "eeg_rest_001",
    "study_name": "Resting-State EEG Connectivity",
    "principal_investigator": "Dr. Bob Wilson",
    "modality": "EEG",
    "session_type": "resting_state",
    "participant_population": "clinical_population",
    "risk_level": "low",
    "duration_minutes": 30,
    "expected_participants": 75
  }
}
```

### Example 3: TMS Safety Study
```json
{
  "session_metadata": {
    "session_id": "tms_safety_001",
    "study_name": "TMS Safety Protocol",
    "principal_investigator": "Dr. Carol Davis",
    "modality": "TMS",
    "session_type": "stimulation",
    "participant_population": "healthy_adults",
    "risk_level": "moderate",
    "duration_minutes": 45,
    "expected_participants": 30
  }
}
```

## Troubleshooting

### Common Issues

#### Disk Space Errors
```bash
# Clean up temporary files
rm -rf /tmp/irb_session_*
```

#### Template Not Found
```bash
# Check template directory structure
ls -la app/templates/
```

#### Validation Errors
- Ensure all required fields are provided
- Check enum values match exactly
- Verify duration and participant counts are positive

### Support
For issues and feature requests, please open an issue on the project repository.

## License
MIT License - See LICENSE file for details

## Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Changelog
### v1.0.0
- Initial release with full IRB session packaging capabilities
- Support for all major imaging modalities
- BIDS-compliant event templates
- Comprehensive IRB documentation
- Multiple export formats

## Contributor Quickstart

```bash
# 1) Create and activate a virtualenv
python3 -m venv .venv && source .venv/bin/activate

# 2) Install dependencies (prefer editable + dev extras)
pip install -U pip
pip install -e .[dev] || pip install -r requirements.txt

# 3) Run locally
uvicorn app.main:app --reload

# 4) Test and quality checks
pytest -q
black . && isort . && flake8 app tests && mypy app

# 5) Conventional Commits
# e.g., feat: add BIDS ZIP export
```
