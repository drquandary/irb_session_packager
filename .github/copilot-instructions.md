# IRB Session Packager

FastAPI web application for creating comprehensive IRB session packages with Standard Operating Procedures (SOPs), IRB documentation, and BIDS templates for imaging research sessions.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap, Build, and Test the Repository
- Create and activate virtual environment:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  ```
- Install dependencies:
  ```bash
  pip install -U pip
  pip install -e .[dev] || pip install -r requirements.txt
  pip install httpx pytest-cov  # Required for testing
  ```
  - **Timing**: Environment setup takes ~30 seconds, dependency installation takes ~60 seconds total. NEVER CANCEL.
  - **Network Issues**: If pip install fails due to network timeouts/firewall limitations, retry multiple times or work with existing environment
  - **Validation Complete**: These instructions have been tested and validated to work correctly
  
- Run the web application:
  ```bash
  uvicorn app.main:app --reload
  ```
  - **Timing**: Server starts in ~5 seconds. NEVER CANCEL development server during testing.
  - **Web Interface**: Access at http://localhost:8000/ 
  - **API**: Access at http://localhost:8000/api/

### Testing
- Run all tests:
  ```bash
  pytest
  ```
  - **Timing**: Tests complete in ~1-4 seconds. NEVER CANCEL. Set timeout to 60+ seconds for safety.
  
- Run tests with coverage:
  ```bash
  pytest --cov=app tests/
  ```
  - **Expected Results**: 21/24 tests pass (3 known failures in export/download functionality that don't affect core features)
  - **Coverage**: ~67% code coverage expected

### Quality Checks
- Run all quality checks (required before committing):
  ```bash
  black . && isort . && flake8 app tests && mypy app
  ```
  - **Timing**: Quality checks take ~10 seconds. NEVER CANCEL. Set timeout to 60+ seconds.
  - **Expected**: Some line length warnings in flake8 are expected and acceptable

## Validation

### Manual Testing Scenarios
After making changes, ALWAYS test these complete scenarios:

1. **Web Interface Functionality**:
   - Navigate to http://localhost:8000/
   - Fill out package creation form with test data
   - Create a package and verify success alert
   - Verify package appears in "Existing Packages" list

2. **API Functionality**:
   ```bash
   # Test health endpoint
   curl http://localhost:8000/api/health
   # Expected: {"status":"ok","service":"IRB Session Packager"}
   
   # Test package creation
   curl -X POST http://localhost:8000/api/create-package \
     -H "Content-Type: application/json" \
     -d '{
       "session_metadata": {
         "session_id": "test_001",
         "study_name": "Test Study", 
         "principal_investigator": "Dr. Test",
         "modality": "fMRI",
         "session_type": "task_based",
         "participant_population": "healthy_adults",
         "risk_level": "minimal",
         "duration_minutes": 60,
         "expected_participants": 20
       },
       "include_sop": true,
       "include_irb": true,
       "include_bids": true
     }'
   # Expected: 200 status with package summary JSON
   ```

3. **Template Generation**:
   - Verify SOP templates are created in `app/templates/sop/`
   - Verify IRB templates are created in `app/templates/irb/` 
   - Verify BIDS templates are created in `app/templates/bids/`

### Build Pipeline Validation
Always run these commands to ensure CI compatibility:
```bash
# Lint checks (matches .github/workflows/ci-cd.yml)
flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
black --check app/
isort --check-only app/
mypy app/ --ignore-missing-imports

# Test execution  
pytest tests/ -v --cov=app --cov-report=xml
```

## Common Tasks

### Repository Structure
```
.
├── README.md                  # Main documentation
├── pyproject.toml            # Build configuration and dependencies
├── requirements.txt          # Runtime dependencies  
├── app/                      # Main application code
│   ├── main.py              # FastAPI application entry point
│   ├── routes.py            # API route definitions
│   ├── models.py            # Pydantic data models
│   ├── packager.py          # Core packaging logic
│   ├── sop_generator.py     # SOP document generation
│   ├── irb_generator.py     # IRB document generation
│   ├── bids_generator.py    # BIDS template generation
│   ├── config.py            # Application configuration
│   ├── common_utils/        # Shared utilities
│   └── templates/           # Document templates
│       ├── sop/            # SOP templates
│       ├── irb/            # IRB document templates
│       ├── bids/           # BIDS templates
│       └── index.html      # Web interface
├── tests/                   # Test files
├── data/                    # Application data storage
└── .github/workflows/       # CI/CD pipelines
```

### Key Configuration Files
- **pyproject.toml**: Primary build config with dependencies and tool settings
- **requirements.txt**: Runtime dependencies (jinja2, reportlab, python-docx, etc.)
- **app/config.py**: Application configuration
- **.github/workflows/ci-cd.yml**: Complete CI/CD pipeline with testing, linting, security, building, and Docker

### Supported Modalities and Options
```python
# Available via GET /api/modalities
MODALITIES = ["fMRI", "EEG", "TMS", "MRI", "PET", "MEG"]
SESSION_TYPES = ["resting_state", "task_based", "stimulation", "clinical", "pilot"]
RISK_LEVELS = ["minimal", "low", "moderate", "high"] 
POPULATIONS = ["healthy_adults", "clinical_population", "children", "elderly", "pregnant"]
```

### Adding New Modalities
1. Add enum value in `app/models.py` (ImagingModality class)
2. Update SOP generator in `app/sop_generator.py` 
3. Add corresponding templates in `app/templates/sop/`
4. Update tests in `tests/test_models.py`

### Known Limitations
- **Export/Download Features**: Some export and download functionality has known issues (3 failing tests)
- **Linting Warnings**: Line length warnings (E501) are common and acceptable for this codebase
- **Pydantic Warnings**: Deprecation warnings about V1 style validators are expected
- **File Operations**: Temporary file paths in tests may fail on different systems

### Environment Variables
```bash
# Optional: Custom template directories
SOP_TEMPLATE_DIR=/custom/sop/templates
IRB_TEMPLATE_DIR=/custom/irb/templates  
BIDS_TEMPLATE_DIR=/custom/bids/templates
```

### API Quick Reference
- `GET /api/health` - Health check
- `GET /api/modalities` - Available options
- `POST /api/create-package` - Create new session package
- `GET /api/package-summary/{session_id}` - Get package summary
- `POST /api/export-package` - Export package (has known issues)
- `GET /api/download-package/{session_id}` - Download package (has known issues)

## Critical Reminders

- **NEVER CANCEL**: All build and test operations complete quickly (~1-60 seconds). Wait for completion.
- **Database**: Application uses SQLite database that auto-creates tables on startup
- **Templates**: Template files are auto-generated on first run if they don't exist
- **Web Interface**: Fully functional for creating and managing packages
- **Code Quality**: Run `black . && isort . && flake8 app tests && mypy app` before committing
- **Testing**: Core functionality (21/24 tests) works reliably; 3 export-related tests have known failures