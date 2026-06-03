import sqlite3
import os
import json
import datetime
import sys
from encryption_stub import EncryptionStub

class DatabaseStub:

    def __init__(self, db_path="room_monitoring.db", nosql_path="telemetry_nosql.jsonl"):
        self.db_path = db_path
        self.nosql_path = nosql_path
        
        # Ensure NoSQL file exists
        if not os.path.exists(self.nosql_path):
            with open(self.nosql_path, "w", encoding="utf-8") as f:
                pass
                
        # Initialize SQL Database
        self._init_sqlite()
        
        # Initialize decryptor for metadata extraction during telemetry routing
        self.encryptor = EncryptionStub()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        with self._get_conn() as conn:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    email TEXT,
                    telegram_id TEXT,
                    assigned_room TEXT,
                    preferred_temp REAL,
                    seniority_weight REAL
                )
            """)
            # Audit logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT
                )
            """)
            # Sensor metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sensor_metadata (
                    room_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                )
            """)
            conn.commit()

            # Populate default users if empty
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                default_users = [
                    ("usr_1", "Admin Operator", "admin", "admin123", "Admin", "admin@smartroom.io", "1947481110", "ROOM_101", 23.0, 1.0),
                    ("usr_2", "Alice", "alice", "alice123", "Resident", "alice@smartroom.io", "", "ROOM_101", 21.0, 1.0),
                    ("usr_3", "Bob", "bob", "bob123", "Resident", "bob@smartroom.io", "", "ROOM_102", 26.0, 1.0),
                    ("usr_4", "Charlie", "charlie", "charlie123", "Resident", "charlie@smartroom.io", "", "ROOM_101", 25.0, 1.0)
                ]
                conn.executemany("""
                    INSERT INTO users (id, name, username, password, role, email, telegram_id, assigned_room, preferred_temp, seniority_weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, default_users)
                conn.commit()
                self.log_audit("System", "Initialization", "Database initialized with default users")

    def get_users(self):
        """Return all users without sensitive password fields."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, username, role, email, telegram_id, assigned_room, preferred_temp, seniority_weight FROM users")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_room_residents(self, room_id):
        """Return all non-Admin residents assigned to a specific room (without passwords)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, username, role, email, telegram_id, assigned_room, preferred_temp, seniority_weight 
                FROM users 
                WHERE assigned_room = ? AND role = 'Resident'
            """, (room_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_user_preference(self, user_id, preferred_temp=None, weight=None):
        """Update a resident's thermal comfort preference or weight."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if preferred_temp is not None and weight is not None:
                cursor.execute("UPDATE users SET preferred_temp = ?, seniority_weight = ? WHERE id = ?", (float(preferred_temp), float(weight), user_id))
            elif preferred_temp is not None:
                cursor.execute("UPDATE users SET preferred_temp = ? WHERE id = ?", (float(preferred_temp), user_id))
            elif weight is not None:
                cursor.execute("UPDATE users SET seniority_weight = ? WHERE id = ?", (float(weight), user_id))
            else:
                return False
            conn.commit()
            return cursor.rowcount > 0

    def lookup_user_by_credentials(self, username, password):
        """Validate login credentials. Returns the user dict (without password) or None."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, username, role, email, telegram_id, assigned_room, preferred_temp, seniority_weight 
                FROM users 
                WHERE username = ? AND password = ?
            """, (username, password))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_user(self, user):
        """Insert new user to the SQL database."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO users (id, name, username, password, role, email, telegram_id, assigned_room, preferred_temp, seniority_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.get("id"),
                user.get("name", "New User"),
                user.get("username", user.get("name", "new_user").lower().replace(" ", "_")),
                user.get("password", "user123"),
                user.get("role", "Resident"),
                user.get("email", ""),
                user.get("telegram_id", ""),
                user.get("assigned_room", "ROOM_101"),
                user.get("preferred_temp", 23.0),
                user.get("seniority_weight", 1.0)
            ))
            conn.commit()

    def remove_user(self, user_id):
        """Remove user from SQL database."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

    def log_audit(self, user_name, action, details=""):
        """Log system/user audit trails to SQL database."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO audit_logs (timestamp, user, action, details)
                VALUES (?, ?, ?, ?)
            """, (timestamp, user_name, action, details))
            conn.commit()

    def get_audit_logs(self):
        """Retrieve system logs from SQL."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, user, action, details FROM audit_logs ORDER BY id DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def insert(self, encrypted_record):
        """
        Validate, route and store telemetry data.
        - Stores encrypted time-series document in NoSQL (JSONL)
        - Extracts room_id & updates status/last_seen in SQL (sensor_metadata)
        """
        try:
            decrypted = self.encryptor.decrypt(encrypted_record)
            room_id = decrypted.get("room_id", "UNKNOWN")
            timestamp = decrypted.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception:
            room_id = "UNKNOWN"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Update SQL (sensor_metadata)
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO sensor_metadata (room_id, status, last_seen)
                VALUES (?, 'ONLINE', ?)
                ON CONFLICT(room_id) DO UPDATE SET status = 'ONLINE', last_seen = excluded.last_seen
            """, (room_id, timestamp))
            conn.commit()

        # 2. Store to NoSQL Time-Series DB (JSONL Document Store)
        doc = {
            "room_id": room_id,
            "timestamp": timestamp,
            "payload": encrypted_record.hex()
        }
        with open(self.nosql_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(doc) + "\n")

    def fetch_all(self):
        """Fetch all historical encrypted telemetry from NoSQL."""
        records = []
        if not os.path.exists(self.nosql_path):
            return records
        
        with open(self.nosql_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    payload_hex = doc.get("payload")
                    if payload_hex:
                        records.append(bytes.fromhex(payload_hex))
                except Exception:
                    continue
        return records

    def latest(self):
        """Fetch the latest encrypted record from NoSQL."""
        records = self.fetch_all()
        return records[-1] if records else None

    def total_records(self):
        """Return total record count in NoSQL database."""
        count = 0
        if not os.path.exists(self.nosql_path):
            return count
        with open(self.nosql_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def clear(self):
        """Clear telemetry in NoSQL and truncate logs/alerts in SQL."""
        # Truncate NoSQL file
        with open(self.nosql_path, "w", encoding="utf-8") as f:
            pass
        
        # Clear SQL tables (excluding users)
        with self._get_conn() as conn:
            conn.execute("DELETE FROM audit_logs")
            conn.execute("DELETE FROM sensor_metadata")
            # We will clear alerts table here too once it's created
            conn.execute("DROP TABLE IF EXISTS alerts")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def size(self):
        """Calculate combined database size."""
        db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        nosql_size = os.path.getsize(self.nosql_path) if os.path.exists(self.nosql_path) else 0
        return db_size + nosql_size

    def health(self):
        """Retrieve system health info for SQL & NoSQL."""
        return {
            "status": "CONNECTED",
            "records": self.total_records(),
            "encrypted_records": self.total_records(),
            "size": self.size()
        }