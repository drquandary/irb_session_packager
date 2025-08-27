from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import yaml
from datetime import datetime
from .models import BIDSEvent, SessionMetadata, ImagingModality, SessionType


class BIDSGenerator:
    """Generates BIDS-compliant event templates and metadata."""
    
    def __init__(self, template_dir: Path = None):
        """Initialize BIDS generator with template directory."""
        if template_dir is None:
            template_dir = Path(__file__).resolve().parent / 'templates' / 'bids'
        
        self.template_dir = template_dir
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default BIDS templates if they don't exist."""
        templates = {
            'task_events.json': self._get_task_events_template(),
            'rest_events.json': self._get_rest_events_template(),
            'dataset_description.json': self._get_dataset_description_template(),
            'participants.json': self._get_participants_template(),
            'README.md': self._get_readme_template(),
            'CHANGES.md': self._get_changes_template()
        }
        
        for filename, content in templates.items():
            template_path = self.template_dir / filename
            if not template_path.exists():
                template_path.write_text(json.dumps(content, indent=2))
    
    def generate_bids_package(self, session_metadata: SessionMetadata, 
                          custom_events: Optional[List[BIDSEvent]] = None) -> Dict[str, Any]:
        """Generate complete BIDS package for the session."""
        
        package = {
            'dataset_description': self._generate_dataset_description(session_metadata),
            'participants': self._generate_participants_template(),
            'events': self._generate_events_template(session_metadata, custom_events),
            'readme': self._generate_readme(session_metadata),
            'changes': self._generate_changes(session_metadata),
            'task_json': self._generate_task_json(session_metadata)
        }
        
        return package
    
    def _generate_dataset_description(self, metadata: SessionMetadata) -> Dict[str, Any]:
        """Generate BIDS dataset_description.json."""
        return {
            "Name": metadata.study_name,
            "BIDSVersion": "1.6.0",
            "Authors": [metadata.principal_investigator],
            "Acknowledgements": "",
            "HowToAcknowledge": "",
            "Funding": [],
            "ReferencesAndLinks": [],
            "DatasetDOI": "",
            "License": "CC0",
            "DatasetType": "raw",
            "EthicsApprovals": ["IRB approved"],
            "DatasetDescription": f"{metadata.modality.value} study investigating brain function in {metadata.participant_population.value.replace('_', ' ')} participants"
        }
    
    def _generate_participants_template(self) -> Dict[str, Any]:
        """Generate BIDS participants.json template."""
        return {
            "participant_id": {
                "Description": "Unique participant identifier",
                "LongName": "Participant ID"
            },
            "age": {
                "Description": "Participant age in years",
                "Units": "years"
            },
            "sex": {
                "Description": "Participant sex",
                "Levels": {
                    "M": "Male",
                    "F": "Female",
                    "O": "Other"
                }
            },
            "group": {
                "Description": "Participant group",
                "Levels": {
                    "control": "Control group",
                    "patient": "Patient group"
                }
            }
        }
    
    def _generate_events_template(self, metadata: SessionMetadata, 
                              custom_events: Optional[List[BIDSEvent]] = None) -> List[BIDSEvent]:
        """Generate appropriate events template based on session type."""
        
        if custom_events:
            return custom_events
        
        if metadata.session_type.value == "task_based":
            return self._generate_task_events(metadata)
        elif metadata.session_type.value == "resting_state":
            return self._generate_rest_events(metadata)
        else:
            return self._generate_generic_events(metadata)
    
    def _generate_task_events(self, metadata: SessionMetadata) -> List[BIDSEvent]:
        """Generate task-based events template."""
        
        # Common task events based on modality
        if metadata.modality == ImagingModality.FMRI:
            return [
                BIDSEvent(onset=0.0, duration=2.0, trial_type="instruction"),
                BIDSEvent(onset=10.0, duration=30.0, trial_type="baseline"),
                BIDSEvent(onset=50.0, duration=2.0, trial_type="cue"),
                BIDSEvent(onset=52.0, duration=4.0, trial_type="stimulus", stimulus_file="stim1.jpg"),
                BIDSEvent(onset=60.0, duration=2.0, trial_type="response"),
                BIDSEvent(onset=70.0, duration=30.0, trial_type="rest"),
                BIDSEvent(onset=110.0, duration=2.0, trial_type="cue"),
                BIDSEvent(onset=112.0, duration=4.0, trial_type="stimulus", stimulus_file="stim2.jpg"),
                BIDSEvent(onset=120.0, duration=2.0, trial_type="response")
            ]
        elif metadata.modality == ImagingModality.EEG:
            return [
                BIDSEvent(onset=0.0, duration=2.0, trial_type="start_recording"),
                BIDSEvent(onset=5.0, duration=300.0, trial_type="eyes_open_rest"),
                BIDSEvent(onset=310.0, duration=2.0, trial_type="instruction"),
                BIDSEvent(onset=315.0, duration=300.0, trial_type="eyes_closed_rest"),
                BIDSEvent(onset=620.0, duration=2.0, trial_type="end_recording")
            ]
        else:
            return self._generate_generic_events(metadata)
    
    def _generate_rest_events(self, metadata: SessionMetadata) -> List[BIDSEvent]:
        """Generate resting-state events template."""
        return [
            BIDSEvent(onset=0.0, duration=2.0, trial_type="start_recording"),
            BIDSEvent(onset=5.0, duration=300.0, trial_type="eyes_open_rest"),
            BIDSEvent(onset=310.0, duration=2.0, trial_type="instruction"),
            BIDSEvent(onset=315.0, duration=300.0, trial_type="eyes_closed_rest"),
            BIDSEvent(onset=620.0, duration=2.0, trial_type="end_recording")
        ]
    
    def _generate_generic_events(self, metadata: SessionMetadata) -> List[BIDSEvent]:
        """Generate generic events template."""
        return [
            BIDSEvent(onset=0.0, duration=2.0, trial_type="start"),
            BIDSEvent(onset=5.0, duration=metadata.duration_minutes*60 - 10, trial_type="data_collection"),
            BIDSEvent(onset=metadata.duration_minutes*60 - 5, duration=2.0, trial_type="end")
        ]
    
    def _generate_task_json(self, metadata: SessionMetadata) -> Dict[str, Any]:
        """Generate task JSON for task-based studies."""
        
        task_name = f"{metadata.modality.value.lower()}_{metadata.session_type.value}"
        
        if metadata.session_type.value == "task_based":
            return {
                "TaskName": task_name,
                "TaskDescription": f"{metadata.modality.value} task-based paradigm",
                "Instructions": "Follow the instructions presented on screen",
                "CogAtlasID": "",
                "CogPOID": "",
                "TaskFullName": f"{metadata.study_name} {metadata.modality.value} Task",
                "TaskVersion": "1.0",
                "TaskCategory": "task",
                "TaskSubcategory": "cognitive",
                "TaskType": "event-related",
                "TaskLength": metadata.duration_minutes * 60,
                "TaskUnits": "seconds"
            }
        elif metadata.session_type.value == "resting_state":
            return {
                "TaskName": "rest",
                "TaskDescription": "Resting-state data collection",
                "Instructions": "Please remain still and relaxed",
                "CogAtlasID": "",
                "CogPOID": "",
                "TaskFullName": "Resting State",
                "TaskVersion": "1.0",
                "TaskCategory": "rest",
                "TaskSubcategory": "resting-state",
                "TaskType": "continuous",
                "TaskLength": metadata.duration_minutes * 60,
                "TaskUnits": "seconds"
            }
        else:
            return {
                "TaskName": metadata.session_type.value,
                "TaskDescription": f"{metadata.modality.value} data collection",
                "Instructions": "Follow researcher instructions",
                "TaskLength": metadata.duration_minutes * 60,
                "TaskUnits": "seconds"
            }
    
    def _generate_readme(self, metadata: SessionMetadata) -> str:
        """Generate BIDS README.md."""
        return f"""# {metadata.study_name}

## Overview
This dataset contains {metadata.modality.value} data collected as part of the {metadata.study_name} study.

## Study Information
- **Principal Investigator**: {metadata.principal_investigator}
- **Modality**: {metadata.modality.value}
- **Session Type**: {metadata.session_type.value.replace('_', ' ').title()}
- **Participant Population**: {metadata.participant_population.value.replace('_', ' ').title()}
- **Expected Participants**: {metadata.expected_participants}
- **Session Duration**: {metadata.duration_minutes} minutes

## Data Structure
This dataset follows the Brain Imaging Data Structure (BIDS) specification.

### Directory Structure
```
{metadata.study_name}/
├── participants.tsv
├── participants.json
├── dataset_description.json
├── README.md
├── CHANGES.md
├── sub-01/
│   └── ses-01/
│       └── {metadata.modality.value.lower()}/
│           ├── sub-01_ses-01_events.tsv
│           └── sub-01_ses-01_events.json
├── sub-02/
│   └── ses-01/
│       └── {metadata.modality.value.lower()}/
│           ├── sub-02_ses-01_events.tsv
│           └── sub-02_ses-01_events.json
└── ...
```

### Files Description
- **participants.tsv**: Participant demographics and grouping information
- **dataset_description.json**: Dataset metadata and BIDS compliance information
- **events.tsv**: Event timing and trial information
- **events.json**: Event metadata and descriptions

## Usage
This dataset can be used with standard BIDS-compatible analysis tools.

## Contact
For questions about this dataset, please contact {metadata.principal_investigator}.
"""
    
    def _generate_changes(self, metadata: SessionMetadata) -> str:
        """Generate BIDS CHANGES.md."""
        return f"""# Changelog
All notable changes to this dataset will be documented in this file.

## [1.0.0] - {datetime.now().strftime('%Y-%m-%d')}
### Added
- Initial dataset creation
- {metadata.modality.value} data collection protocol
- BIDS-compliant structure
- Participant recruitment materials

### Study Details
- Study: {metadata.study_name}
- PI: {metadata.principal_investigator}
- Modality: {metadata.modality.value}
- Expected participants: {metadata.expected_participants}
"""
    
    def _get_task_events_template(self) -> Dict[str, Any]:
        """Get task events template."""
        return {
            "onset": {"Description": "Onset time of the event in seconds"},
            "duration": {"Description": "Duration of the event in seconds"},
            "trial_type": {
                "Description": "Type of trial",
                "Levels": {
                    "instruction": "Instruction presentation",
                    "baseline": "Baseline period",
                    "cue": "Cue presentation",
                    "stimulus": "Stimulus presentation",
                    "response": "Response period",
                    "rest": "Rest period"
                }
            },
            "response_time": {"Description": "Response time in milliseconds"},
            "accuracy": {"Description": "Accuracy of response (1=correct, 0=incorrect)"},
            "stimulus_file": {"Description": "Path to stimulus file"}
        }
    
    def _get_rest_events_template(self) -> Dict[str, Any]:
        """Get resting-state events template."""
        return {
            "onset": {"Description": "Onset time of the event in seconds"},
            "duration": {"Description": "Duration of the event in seconds"},
            "trial_type": {
                "Description": "Type of resting state period",
                "Levels": {
                    "start_recording": "Start of data recording",
                    "eyes_open_rest": "Eyes open resting state",
                    "eyes_closed_rest": "Eyes closed resting state",
                    "instruction": "Instruction presentation",
                    "end_recording": "End of data recording"
                }
            }
        }
    
    def _get_dataset_description_template(self) -> Dict[str, Any]:
        """Get dataset_description.json template."""
        return {
            "Name": "Study Name",
            "BIDSVersion": "1.6.0",
            "Authors": ["Principal Investigator"],
            "Acknowledgements": "",
            "HowToAcknowledge": "",
            "Funding": [],
            "ReferencesAndLinks": [],
            "DatasetDOI": "",
            "License": "CC0",
            "DatasetType": "raw",
            "EthicsApprovals": ["IRB approved"],
            "DatasetDescription": "BIDS-compliant neuroimaging dataset"
        }
    
    def _get_participants_template(self) -> Dict[str, Any]:
        """Get participants.json template."""
        return {
            "participant_id": {
                "Description": "Unique participant identifier",
                "LongName": "Participant ID"
            },
            "age": {
                "Description": "Participant age in years",
                "Units": "years"
            },
            "sex": {
                "Description": "Participant sex",
                "Levels": {
                    "M": "Male",
                    "F": "Female",
                    "O": "Other"
                }
            },
            "group": {
                "Description": "Participant group",
                "Levels": {
                    "control": "Control group",
                    "patient": "Patient group"
                }
            }
        }
    
    def _get_readme_template(self) -> str:
        """Get README.md template."""
        return """# Study Name

## Overview
This dataset contains neuroimaging data collected as part of [Study Name].

## Data Structure
This dataset follows the Brain Imaging Data Structure (BIDS) specification.

## Directory Structure
```
study_name/
├── participants.tsv
├── participants.json
├── dataset_description.json
├── README.md
├── CHANGES.md
├── sub-01/
│   └── ses-01/
│       └── modality/
│           ├── sub-01_ses-01_events.tsv
│           └── sub-01_ses-01_events.json
└── ...
```

## Usage
This dataset can be used with standard BIDS-compatible analysis tools.

## Contact
For questions about this dataset, please contact [contact information].
"""
    
    def _get_changes_template(self) -> str:
        """Get CHANGES.md template."""
        return """# Changelog
All notable changes to this dataset will be documented in this file.

## [1.0.0] - YYYY-MM-DD
### Added
- Initial dataset creation
- BIDS-compliant structure
- Participant recruitment materials
"""
    
    def export_bids_package(self, session_metadata: SessionMetadata, 
                          output_dir: Path, custom_events: Optional[List[BIDSEvent]] = None) -> Path:
        """Export complete BIDS package to directory."""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate package
        package = self.generate_bids_package(session_metadata, custom_events)
        
        # Write files
        (output_dir / "dataset_description.json").write_text(
            json.dumps(package['dataset_description'], indent=2)
        )
        
        (output_dir / "participants.json").write_text(
            json.dumps(package['participants'], indent=2)
        )
        
        (output_dir / "participants.tsv").write_text(
            "participant_id\tage\tsex\tgroup\n"
        )
        
        (output_dir / "README.md").write_text(package['readme'])
        (output_dir / "CHANGES.md").write_text(package['changes'])
        
        # Create task JSON
        task_json = package['task_json']
        task_name = task_json['TaskName']
        (output_dir / f"task-{task_name}_bold.json").write_text(
            json.dumps(task_json, indent=2)
        )
        
        # Create events template
        events = package['events']
        if events:
            events_tsv = "onset\tduration\ttrial_type\tresponse_time\taccuracy\tstimulus_file\n"
            for event in events:
                events_tsv += f"{event.onset}\t{event.duration}\t{event.trial_type}\t"
                events_tsv += f"{event.response_time or ''}\t{event.accuracy or ''}\t{event.stimulus_file or ''}\n"
            
            (output_dir / f"task-{task_name}_events.tsv").write_text(events_tsv)
            (output_dir / f"task-{task_name}_events.json").write_text(
                json.dumps(self._get_task_events_template(), indent=2)
            )
        
        return output_dir
