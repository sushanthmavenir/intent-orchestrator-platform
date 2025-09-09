import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from pathlib import Path


class IntentDatabase:
    def __init__(self, db_path: str = "data/intents.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS intents (
                    id TEXT PRIMARY KEY,
                    href TEXT,
                    creation_date TEXT NOT NULL,
                    description TEXT,
                    last_update TEXT NOT NULL,
                    lifecycle_status TEXT DEFAULT 'created',
                    name TEXT,
                    status_change_date TEXT NOT NULL,
                    version TEXT DEFAULT '1.0',
                    expression_data TEXT,
                    valid_for_start TEXT,
                    valid_for_end TEXT,
                    base_type TEXT,
                    schema_location TEXT,
                    type TEXT
                );
                
                CREATE TABLE IF NOT EXISTS intent_reports (
                    id TEXT PRIMARY KEY,
                    href TEXT,
                    creation_date TEXT NOT NULL,
                    description TEXT,
                    name TEXT,
                    expression_data TEXT,
                    intent_id TEXT NOT NULL,
                    intent_data TEXT,
                    valid_for_start TEXT,
                    valid_for_end TEXT,
                    base_type TEXT,
                    schema_location TEXT,
                    type TEXT,
                    FOREIGN KEY (intent_id) REFERENCES intents (id)
                );
                
                CREATE TABLE IF NOT EXISTS event_subscriptions (
                    id TEXT PRIMARY KEY,
                    callback TEXT NOT NULL,
                    query TEXT,
                    created_at TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_intents_lifecycle_status ON intents(lifecycle_status);
                CREATE INDEX IF NOT EXISTS idx_intents_name ON intents(name);
                CREATE INDEX IF NOT EXISTS idx_intent_reports_intent_id ON intent_reports(intent_id);
            """)
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_intent(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            expression_json = None
            if intent_data.get("expression"):
                expression_json = json.dumps(intent_data["expression"])
            
            valid_for = intent_data.get("validFor") or intent_data.get("valid_for")
            valid_for_start = valid_for.get("startDateTime") if valid_for else None
            valid_for_end = valid_for.get("endDateTime") if valid_for else None
            
            cursor.execute("""
                INSERT INTO intents (
                    id, href, creation_date, description, last_update,
                    lifecycle_status, name, status_change_date, version,
                    expression_data, valid_for_start, valid_for_end,
                    base_type, schema_location, type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intent_data["id"],
                intent_data.get("href"),
                intent_data["creation_date"].isoformat() if isinstance(intent_data["creation_date"], datetime) else intent_data["creation_date"],
                intent_data.get("description"),
                intent_data["last_update"].isoformat() if isinstance(intent_data["last_update"], datetime) else intent_data["last_update"],
                intent_data.get("lifecycle_status", "created"),
                intent_data.get("name"),
                intent_data["status_change_date"].isoformat() if isinstance(intent_data["status_change_date"], datetime) else intent_data["status_change_date"],
                intent_data.get("version", "1.0"),
                expression_json,
                valid_for_start,
                valid_for_end,
                intent_data.get("@baseType"),
                intent_data.get("@schemaLocation"),
                intent_data.get("@type")
            ))
            conn.commit()
            return self.get_intent(intent_data["id"])
    
    def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM intents WHERE id = ?", (intent_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            intent = dict(row)
            
            if intent["expression_data"]:
                intent["expression"] = json.loads(intent["expression_data"])
            
            if intent["valid_for_start"] or intent["valid_for_end"]:
                intent["validFor"] = {}
                if intent["valid_for_start"]:
                    intent["validFor"]["startDateTime"] = intent["valid_for_start"]
                if intent["valid_for_end"]:
                    intent["validFor"]["endDateTime"] = intent["valid_for_end"]
            
            intent.pop("expression_data", None)
            intent.pop("valid_for_start", None)
            intent.pop("valid_for_end", None)
            
            if intent.get("@baseType") is None:
                intent.pop("@baseType", None)
            if intent.get("@schemaLocation") is None:
                intent.pop("@schemaLocation", None)
            if intent.get("@type") is None:
                intent.pop("@type", None)
            
            return intent
    
    def list_intents(self, offset: int = 0, limit: Optional[int] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = ""
            params = []
            
            if filters:
                conditions = []
                if filters.get("lifecycle_status"):
                    conditions.append("lifecycle_status = ?")
                    params.append(filters["lifecycle_status"])
                if filters.get("name"):
                    conditions.append("name LIKE ?")
                    params.append(f"%{filters['name']}%")
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            count_query = f"SELECT COUNT(*) FROM intents {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            query = f"SELECT * FROM intents {where_clause} ORDER BY creation_date DESC"
            if limit is not None:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            intents = []
            for row in rows:
                intent = dict(row)
                if intent["expression_data"]:
                    intent["expression"] = json.loads(intent["expression_data"])
                
                if intent["valid_for_start"] or intent["valid_for_end"]:
                    intent["validFor"] = {}
                    if intent["valid_for_start"]:
                        intent["validFor"]["startDateTime"] = intent["valid_for_start"]
                    if intent["valid_for_end"]:
                        intent["validFor"]["endDateTime"] = intent["valid_for_end"]
                
                intent.pop("expression_data", None)
                intent.pop("valid_for_start", None)
                intent.pop("valid_for_end", None)
                
                if intent.get("@baseType") is None:
                    intent.pop("@baseType", None)
                if intent.get("@schemaLocation") is None:
                    intent.pop("@schemaLocation", None)
                if intent.get("@type") is None:
                    intent.pop("@type", None)
                
                intents.append(intent)
            
            return {
                "items": intents,
                "total_count": total_count,
                "result_count": len(intents),
                "offset": offset,
                "limit": limit
            }
    
    def update_intent(self, intent_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            existing_intent = self.get_intent(intent_id)
            if not existing_intent:
                return None
            
            update_fields = []
            params = []
            
            for field in ["description", "lifecycle_status", "name", "version"]:
                if field in update_data:
                    update_fields.append(f"{field} = ?")
                    params.append(update_data[field])
            
            if "expression" in update_data:
                update_fields.append("expression_data = ?")
                params.append(json.dumps(update_data["expression"]))
            
            if "validFor" in update_data or "valid_for" in update_data:
                valid_for = update_data.get("validFor") or update_data.get("valid_for")
                update_fields.append("valid_for_start = ?")
                update_fields.append("valid_for_end = ?")
                params.extend([
                    valid_for.get("startDateTime") if valid_for else None,
                    valid_for.get("endDateTime") if valid_for else None
                ])
            
            update_fields.append("last_update = ?")
            params.append(datetime.utcnow().isoformat())
            
            params.append(intent_id)
            
            query = f"UPDATE intents SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            return self.get_intent(intent_id)
    
    def delete_intent(self, intent_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM intent_reports WHERE intent_id = ?", (intent_id,))
            cursor.execute("DELETE FROM intents WHERE id = ?", (intent_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def create_intent_report(self, intent_id: str, report_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.get_intent(intent_id):
            return None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            expression_json = None
            if report_data.get("expression"):
                expression_json = json.dumps(report_data["expression"])
            
            intent_json = None
            if report_data.get("intent"):
                intent_json = json.dumps(report_data["intent"])
            
            valid_for = report_data.get("validFor") or report_data.get("valid_for")
            valid_for_start = valid_for.get("startDateTime") if valid_for else None
            valid_for_end = valid_for.get("endDateTime") if valid_for else None
            
            cursor.execute("""
                INSERT INTO intent_reports (
                    id, href, creation_date, description, name,
                    expression_data, intent_id, intent_data,
                    valid_for_start, valid_for_end,
                    base_type, schema_location, type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_data["id"],
                report_data.get("href"),
                report_data["creation_date"].isoformat() if isinstance(report_data["creation_date"], datetime) else report_data["creation_date"],
                report_data.get("description"),
                report_data.get("name"),
                expression_json,
                intent_id,
                intent_json,
                valid_for_start,
                valid_for_end,
                report_data.get("@baseType"),
                report_data.get("@schemaLocation"),
                report_data.get("@type")
            ))
            conn.commit()
            return self.get_intent_report(intent_id, report_data["id"])
    
    def get_intent_report(self, intent_id: str, report_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM intent_reports WHERE intent_id = ? AND id = ?",
                (intent_id, report_id)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            report = dict(row)
            
            if report["expression_data"]:
                report["expression"] = json.loads(report["expression_data"])
            
            if report["intent_data"]:
                report["intent"] = json.loads(report["intent_data"])
            
            if report["valid_for_start"] or report["valid_for_end"]:
                report["validFor"] = {}
                if report["valid_for_start"]:
                    report["validFor"]["startDateTime"] = report["valid_for_start"]
                if report["valid_for_end"]:
                    report["validFor"]["endDateTime"] = report["valid_for_end"]
            
            report.pop("expression_data", None)
            report.pop("intent_data", None)
            report.pop("valid_for_start", None)
            report.pop("valid_for_end", None)
            report.pop("intent_id", None)
            
            return report
    
    def list_intent_reports(self, intent_id: str, offset: int = 0, limit: Optional[int] = None) -> Dict[str, Any]:
        if not self.get_intent(intent_id):
            return {"items": [], "total_count": 0, "result_count": 0, "offset": offset, "limit": limit}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM intent_reports WHERE intent_id = ?", (intent_id,))
            total_count = cursor.fetchone()[0]
            
            query = "SELECT * FROM intent_reports WHERE intent_id = ? ORDER BY creation_date DESC"
            params = [intent_id]
            
            if limit is not None:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                report = dict(row)
                if report["expression_data"]:
                    report["expression"] = json.loads(report["expression_data"])
                
                if report["intent_data"]:
                    report["intent"] = json.loads(report["intent_data"])
                
                if report["valid_for_start"] or report["valid_for_end"]:
                    report["validFor"] = {}
                    if report["valid_for_start"]:
                        report["validFor"]["startDateTime"] = report["valid_for_start"]
                    if report["valid_for_end"]:
                        report["validFor"]["endDateTime"] = report["valid_for_end"]
                
                report.pop("expression_data", None)
                report.pop("intent_data", None)
                report.pop("valid_for_start", None)
                report.pop("valid_for_end", None)
                report.pop("intent_id", None)
                
                reports.append(report)
            
            return {
                "items": reports,
                "total_count": total_count,
                "result_count": len(reports),
                "offset": offset,
                "limit": limit
            }
    
    def delete_intent_report(self, intent_id: str, report_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM intent_reports WHERE intent_id = ? AND id = ?",
                (intent_id, report_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO event_subscriptions (id, callback, query, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                subscription_data["id"],
                subscription_data["callback"],
                subscription_data.get("query"),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            return subscription_data
    
    def delete_subscription(self, subscription_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM event_subscriptions WHERE id = ?", (subscription_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_subscriptions(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM event_subscriptions")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]