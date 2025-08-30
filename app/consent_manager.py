"""Dynamic consent management module for IRB Session Packager."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from .models import (
    DynamicConsent, ConsentStatus, ConsentType, 
    ParticipantCommunication, SessionMetadata
)
from .common_utils.database import DatabaseConnection


class ConsentManager:
    """Manages dynamic consent for research participants."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize consent manager with database storage."""
        if storage_path is None:
            storage_path = Path("./data/consent.db")
        
        self.storage_db = DatabaseConnection(storage_path)
        self._init_storage()
    
    def _init_storage(self):
        """Initialize consent database tables."""
        schema = {
            "consents": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "participant_id": "TEXT NOT NULL",
                "consent_data": "TEXT NOT NULL",  # JSON string
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            "communications": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "participant_id": "TEXT NOT NULL",
                "communication_data": "TEXT NOT NULL",  # JSON string
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
        }
        
        for table_name, table_schema in schema.items():
            self.storage_db.create_table(table_name, table_schema)
    
    def create_consent(self, consent: DynamicConsent) -> bool:
        """Create or update participant consent."""
        try:
            # Convert consent to dict and handle datetime serialization
            consent_dict = consent.model_dump()
            consent_dict['consent_date'] = consent_dict['consent_date'].isoformat()
            consent_dict['last_updated'] = consent_dict['last_updated'].isoformat()
            if consent_dict.get('withdrawal_date'):
                consent_dict['withdrawal_date'] = consent_dict['withdrawal_date'].isoformat()
            
            # Convert enum keys to strings for JSON serialization
            consent_dict['consent_permissions'] = {
                k.value if hasattr(k, 'value') else str(k): v.value if hasattr(v, 'value') else str(v)
                for k, v in consent.consent_permissions.items()
            }
            
            consent_json = json.dumps(consent_dict)
            
            # Check if consent already exists
            existing = self.storage_db.execute_query(
                "SELECT id FROM consents WHERE participant_id = ?",
                (consent.participant_id,)
            )
            
            if existing:
                # Update existing consent
                self.storage_db.execute_update(
                    "UPDATE consents SET consent_data = ?, updated_at = CURRENT_TIMESTAMP WHERE participant_id = ?",
                    (consent_json, consent.participant_id)
                )
            else:
                # Create new consent
                self.storage_db.execute_update(
                    "INSERT INTO consents (participant_id, consent_data) VALUES (?, ?)",
                    (consent.participant_id, consent_json)
                )
            
            return True
        except Exception as e:
            print(f"Error creating consent: {e}")
            return False
    
    def get_consent(self, participant_id: str) -> Optional[DynamicConsent]:
        """Retrieve participant consent."""
        try:
            results = self.storage_db.execute_query(
                "SELECT consent_data FROM consents WHERE participant_id = ?",
                (participant_id,)
            )
            
            if not results:
                return None
            
            consent_dict = json.loads(results[0]["consent_data"])
            
            # Convert datetime strings back to datetime objects
            consent_dict['consent_date'] = datetime.fromisoformat(consent_dict['consent_date'])
            consent_dict['last_updated'] = datetime.fromisoformat(consent_dict['last_updated'])
            if consent_dict.get('withdrawal_date'):
                consent_dict['withdrawal_date'] = datetime.fromisoformat(consent_dict['withdrawal_date'])
            
            # Convert consent permissions back to enums
            consent_permissions = {}
            for k, v in consent_dict['consent_permissions'].items():
                consent_type = ConsentType(k)
                consent_status = ConsentStatus(v)
                consent_permissions[consent_type] = consent_status
            consent_dict['consent_permissions'] = consent_permissions
            
            return DynamicConsent(**consent_dict)
        
        except Exception as e:
            print(f"Error retrieving consent: {e}")
            return None
    
    def update_consent_status(self, participant_id: str, consent_type: ConsentType, 
                            new_status: ConsentStatus) -> bool:
        """Update specific consent permission status."""
        try:
            consent = self.get_consent(participant_id)
            if not consent:
                return False
            
            consent.consent_permissions[consent_type] = new_status
            consent.last_updated = datetime.now()
            
            if new_status == ConsentStatus.WITHDRAWN:
                consent.withdrawal_date = datetime.now()
            
            return self.create_consent(consent)
        
        except Exception as e:
            print(f"Error updating consent status: {e}")
            return False
    
    def withdraw_all_consent(self, participant_id: str, reason: Optional[str] = None) -> bool:
        """Withdraw all consent permissions for a participant."""
        try:
            consent = self.get_consent(participant_id)
            if not consent:
                return False
            
            # Set all permissions to withdrawn
            for consent_type in consent.consent_permissions:
                consent.consent_permissions[consent_type] = ConsentStatus.WITHDRAWN
            
            consent.withdrawal_date = datetime.now()
            consent.last_updated = datetime.now()
            if reason:
                consent.notes = f"Full withdrawal: {reason}"
            
            return self.create_consent(consent)
        
        except Exception as e:
            print(f"Error withdrawing consent: {e}")
            return False
    
    def check_consent_validity(self, participant_id: str, session_metadata: SessionMetadata) -> Dict[str, Any]:
        """Check if participant consent is valid for the given session."""
        consent = self.get_consent(participant_id)
        if not consent:
            return {
                "valid": False,
                "reason": "No consent record found",
                "required_actions": ["Obtain initial consent"]
            }
        
        # Check if any permissions are withdrawn
        withdrawn_permissions = [
            perm.value for perm, status in consent.consent_permissions.items()
            if status == ConsentStatus.WITHDRAWN
        ]
        
        if withdrawn_permissions:
            return {
                "valid": False,
                "reason": f"Withdrawn permissions: {', '.join(withdrawn_permissions)}",
                "required_actions": ["Re-consent for withdrawn permissions"]
            }
        
        # Check for expired consent (assuming 2-year validity)
        if consent.consent_date < datetime.now() - timedelta(days=730):
            return {
                "valid": False,
                "reason": "Consent has expired",
                "required_actions": ["Renew consent"]
            }
        
        return {
            "valid": True,
            "consent_date": consent.consent_date,
            "permissions": consent.consent_permissions
        }
    
    def get_participants_by_consent_status(self, consent_type: ConsentType, 
                                         status: ConsentStatus) -> List[str]:
        """Get list of participants with specific consent status."""
        try:
            results = self.storage_db.execute_query(
                "SELECT participant_id, consent_data FROM consents"
            )
            
            matching_participants = []
            for row in results:
                consent_dict = json.loads(row["consent_data"])
                consent = DynamicConsent(**consent_dict)
                
                if consent.consent_permissions.get(consent_type) == status:
                    matching_participants.append(consent.participant_id)
            
            return matching_participants
        
        except Exception as e:
            print(f"Error querying consent status: {e}")
            return []
    
    def log_communication(self, communication: ParticipantCommunication) -> bool:
        """Log participant communication for compliance tracking."""
        try:
            comm_json = communication.model_dump_json()
            self.storage_db.execute_update(
                "INSERT INTO communications (participant_id, communication_data) VALUES (?, ?)",
                (communication.participant_id, comm_json)
            )
            return True
        
        except Exception as e:
            print(f"Error logging communication: {e}")
            return False
    
    def get_communication_history(self, participant_id: str) -> List[ParticipantCommunication]:
        """Get communication history for a participant."""
        try:
            results = self.storage_db.execute_query(
                "SELECT communication_data FROM communications WHERE participant_id = ? ORDER BY created_at DESC",
                (participant_id,)
            )
            
            communications = []
            for row in results:
                comm_dict = json.loads(row["communication_data"])
                communications.append(ParticipantCommunication(**comm_dict))
            
            return communications
        
        except Exception as e:
            print(f"Error retrieving communication history: {e}")
            return []
    
    def generate_consent_report(self) -> Dict[str, Any]:
        """Generate summary report of consent status across all participants."""
        try:
            results = self.storage_db.execute_query("SELECT consent_data FROM consents")
            
            total_participants = len(results)
            consent_summary = {
                consent_type.value: {
                    status.value: 0 for status in ConsentStatus
                } for consent_type in ConsentType
            }
            
            withdrawn_count = 0
            expired_count = 0
            
            for row in results:
                consent_dict = json.loads(row["consent_data"])
                consent = DynamicConsent(**consent_dict)
                
                # Count consent status by type
                for consent_type, status in consent.consent_permissions.items():
                    consent_summary[consent_type.value][status.value] += 1
                
                # Check for any withdrawn permissions
                if any(status == ConsentStatus.WITHDRAWN for status in consent.consent_permissions.values()):
                    withdrawn_count += 1
                
                # Check for expired consent
                if consent.consent_date < datetime.now() - timedelta(days=730):
                    expired_count += 1
            
            return {
                "total_participants": total_participants,
                "consent_summary": consent_summary,
                "participants_with_withdrawals": withdrawn_count,
                "participants_with_expired_consent": expired_count,
                "report_generated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Error generating consent report: {e}")
            return {"error": str(e)}