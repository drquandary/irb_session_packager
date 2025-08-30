"""Audit and version control module for IRB Session Packager."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid
from .models import AuditEntry, SessionMetadata, IRBDocument
from .common_utils.database import DatabaseConnection


class AuditManager:
    """Manages audit trails and version control for IRB documents."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize audit manager with database storage."""
        if storage_path is None:
            storage_path = Path("./data/audit.db")
        
        self.storage_db = DatabaseConnection(storage_path)
        self._init_storage()
    
    def _init_storage(self):
        """Initialize audit database tables."""
        schema = {
            "audit_entries": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "entry_id": "TEXT UNIQUE NOT NULL",
                "session_id": "TEXT NOT NULL",
                "action": "TEXT NOT NULL",
                "user_id": "TEXT NOT NULL",
                "version": "TEXT NOT NULL",
                "changes": "TEXT NOT NULL",  # JSON string
                "timestamp": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            "document_versions": {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "session_id": "TEXT NOT NULL",
                "document_type": "TEXT NOT NULL",
                "version": "TEXT NOT NULL",
                "content": "TEXT NOT NULL",
                "created_by": "TEXT NOT NULL",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
        }
        
        for table_name, table_schema in schema.items():
            self.storage_db.create_table(table_name, table_schema)
    
    def create_audit_entry(self, session_id: str, action: str, user_id: str, 
                          changes: Dict[str, Any], version: str) -> str:
        """Create a new audit entry and return the entry ID."""
        try:
            entry_id = str(uuid.uuid4())
            changes_json = json.dumps(changes)
            
            audit_entry = AuditEntry(
                entry_id=entry_id,
                session_id=session_id,
                action=action,
                user_id=user_id,
                changes=changes,
                version=version
            )
            
            self.storage_db.execute_update(
                "INSERT INTO audit_entries (entry_id, session_id, action, user_id, version, changes) VALUES (?, ?, ?, ?, ?, ?)",
                (entry_id, session_id, action, user_id, version, changes_json)
            )
            
            return entry_id
        
        except Exception as e:
            print(f"Error creating audit entry: {e}")
            return ""
    
    def log_document_creation(self, session_id: str, user_id: str, 
                            document: IRBDocument) -> str:
        """Log the creation of a new IRB document."""
        changes = {
            "action": "document_created",
            "document_type": document.document_type,
            "document_version": document.version,
            "content_length": len(document.content),
            "approved": document.approved
        }
        
        # Store document version
        self._store_document_version(session_id, document, user_id)
        
        return self.create_audit_entry(
            session_id=session_id,
            action="create_document",
            user_id=user_id,
            changes=changes,
            version=document.version
        )
    
    def log_document_modification(self, session_id: str, user_id: str, 
                                old_document: IRBDocument, new_document: IRBDocument) -> str:
        """Log the modification of an IRB document."""
        changes = {
            "action": "document_modified",
            "document_type": new_document.document_type,
            "old_version": old_document.version,
            "new_version": new_document.version,
            "old_content_length": len(old_document.content),
            "new_content_length": len(new_document.content),
            "content_changed": old_document.content != new_document.content,
            "approval_status_changed": old_document.approved != new_document.approved
        }
        
        # Store new document version
        self._store_document_version(session_id, new_document, user_id)
        
        return self.create_audit_entry(
            session_id=session_id,
            action="modify_document",
            user_id=user_id,
            changes=changes,
            version=new_document.version
        )
    
    def log_approval_status_change(self, session_id: str, user_id: str, 
                                 document_type: str, approved: bool, 
                                 version: str, notes: Optional[str] = None) -> str:
        """Log IRB approval status changes."""
        changes = {
            "action": "approval_status_change",
            "document_type": document_type,
            "approved": approved,
            "notes": notes or "",
            "approval_date": datetime.now().isoformat() if approved else None
        }
        
        return self.create_audit_entry(
            session_id=session_id,
            action="approval_change",
            user_id=user_id,
            changes=changes,
            version=version
        )
    
    def log_session_package_creation(self, session_id: str, user_id: str, 
                                   package_metadata: SessionMetadata) -> str:
        """Log the creation of a session package."""
        changes = {
            "action": "session_package_created",
            "study_name": package_metadata.study_name,
            "principal_investigator": package_metadata.principal_investigator,
            "modality": package_metadata.modality.value,
            "session_type": package_metadata.session_type.value,
            "risk_level": package_metadata.risk_level.value,
            "participant_population": package_metadata.participant_population.value,
            "duration_minutes": package_metadata.duration_minutes,
            "expected_participants": package_metadata.expected_participants
        }
        
        return self.create_audit_entry(
            session_id=session_id,
            action="create_package",
            user_id=user_id,
            changes=changes,
            version="1.0"
        )
    
    def _store_document_version(self, session_id: str, document: IRBDocument, user_id: str):
        """Store a versioned copy of a document."""
        try:
            self.storage_db.execute_update(
                "INSERT INTO document_versions (session_id, document_type, version, content, created_by) VALUES (?, ?, ?, ?, ?)",
                (session_id, document.document_type, document.version, document.content, user_id)
            )
        except Exception as e:
            print(f"Error storing document version: {e}")
    
    def get_audit_trail(self, session_id: str) -> List[AuditEntry]:
        """Get complete audit trail for a session."""
        try:
            results = self.storage_db.execute_query(
                "SELECT entry_id, session_id, action, user_id, version, changes, timestamp FROM audit_entries WHERE session_id = ? ORDER BY timestamp DESC",
                (session_id,)
            )
            
            audit_entries = []
            for row in results:
                changes_dict = json.loads(row["changes"])
                entry = AuditEntry(
                    entry_id=row["entry_id"],
                    session_id=row["session_id"],
                    action=row["action"],
                    user_id=row["user_id"],
                    version=row["version"],
                    changes=changes_dict,
                    timestamp=datetime.fromisoformat(row["timestamp"].replace(' ', 'T'))
                )
                audit_entries.append(entry)
            
            return audit_entries
        
        except Exception as e:
            print(f"Error retrieving audit trail: {e}")
            return []
    
    def get_document_versions(self, session_id: str, document_type: str) -> List[Dict[str, Any]]:
        """Get all versions of a specific document."""
        try:
            results = self.storage_db.execute_query(
                "SELECT version, content, created_by, created_at FROM document_versions WHERE session_id = ? AND document_type = ? ORDER BY created_at DESC",
                (session_id, document_type)
            )
            
            versions = []
            for row in results:
                versions.append({
                    "version": row["version"],
                    "content": row["content"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"]
                })
            
            return versions
        
        except Exception as e:
            print(f"Error retrieving document versions: {e}")
            return []
    
    def get_latest_document_version(self, session_id: str, document_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest version of a specific document."""
        versions = self.get_document_versions(session_id, document_type)
        return versions[0] if versions else None
    
    def compare_document_versions(self, session_id: str, document_type: str, 
                                version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions of a document."""
        try:
            results = self.storage_db.execute_query(
                "SELECT version, content FROM document_versions WHERE session_id = ? AND document_type = ? AND version IN (?, ?)",
                (session_id, document_type, version1, version2)
            )
            
            if len(results) != 2:
                return {"error": "Could not find both versions for comparison"}
            
            version_data = {row["version"]: row["content"] for row in results}
            
            content1 = version_data.get(version1, "")
            content2 = version_data.get(version2, "")
            
            # Simple comparison metrics
            lines1 = content1.split('\n')
            lines2 = content2.split('\n')
            
            return {
                "version1": version1,
                "version2": version2,
                "content1_length": len(content1),
                "content2_length": len(content2),
                "lines1_count": len(lines1),
                "lines2_count": len(lines2),
                "content_identical": content1 == content2,
                "length_difference": len(content2) - len(content1),
                "line_difference": len(lines2) - len(lines1)
            }
        
        except Exception as e:
            print(f"Error comparing document versions: {e}")
            return {"error": str(e)}
    
    def generate_audit_report(self, session_id: Optional[str] = None, 
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        try:
            query = "SELECT * FROM audit_entries WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC"
            
            results = self.storage_db.execute_query(query, tuple(params))
            
            # Aggregate statistics
            action_counts = {}
            user_activity = {}
            session_activity = {}
            
            for row in results:
                action = row["action"]
                user_id = row["user_id"]
                session_id = row["session_id"]
                
                action_counts[action] = action_counts.get(action, 0) + 1
                user_activity[user_id] = user_activity.get(user_id, 0) + 1
                session_activity[session_id] = session_activity.get(session_id, 0) + 1
            
            return {
                "total_entries": len(results),
                "action_counts": action_counts,
                "user_activity": user_activity,
                "session_activity": session_activity,
                "most_active_user": max(user_activity.items(), key=lambda x: x[1]) if user_activity else None,
                "most_active_session": max(session_activity.items(), key=lambda x: x[1]) if session_activity else None,
                "report_period": {
                    "start": start_date.isoformat() if start_date else "all time",
                    "end": end_date.isoformat() if end_date else "now"
                },
                "generated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Error generating audit report: {e}")
            return {"error": str(e)}
    
    def get_sessions_by_user(self, user_id: str) -> List[str]:
        """Get list of session IDs that a user has worked on."""
        try:
            results = self.storage_db.execute_query(
                "SELECT DISTINCT session_id FROM audit_entries WHERE user_id = ?",
                (user_id,)
            )
            
            return [row["session_id"] for row in results]
        
        except Exception as e:
            print(f"Error retrieving sessions by user: {e}")
            return []