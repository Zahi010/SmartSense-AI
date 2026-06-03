from datetime import datetime
import sqlite3

class AlertHistory:

    def __init__(self, db_path="room_monitoring.db"):
        self.db_path = db_path
        # Ensure the table is created
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
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

    def add(self, room, alerts):
        with self._get_conn() as conn:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for alert in alerts:
                severity = "INFO"
                if "Temperature" in alert:
                    severity = "CRITICAL"
                elif "Humidity" in alert:
                    severity = "WARNING"
                elif "Air Quality" in alert:
                    severity = "WARNING"
                elif "Motion" in alert:
                    severity = "INFO"

                conn.execute("""
                    INSERT INTO alerts (room_id, alert_type, message, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (room, severity, alert, timestamp))
            conn.commit()

    def recent(self, limit=5):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT room_id as room, message as alert, alert_type as severity, timestamp as time 
                FROM alerts 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            # Convert timestamp to time string %H:%M:%S for UI display compatibility if needed
            result = []
            for row in rows:
                r_dict = dict(row)
                try:
                    dt = datetime.strptime(r_dict["time"], "%Y-%m-%d %H:%M:%S")
                    r_dict["time"] = dt.strftime("%H:%M:%S")
                except Exception:
                    pass
                result.append(r_dict)
            return list(reversed(result))

    def summary(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT alert_type, COUNT(*) as count FROM alerts GROUP BY alert_type")
            rows = cursor.fetchall()
            counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
            for row in rows:
                counts[row["alert_type"]] = row["count"]
            
            total = sum(counts.values())
            return {
                "critical": counts["CRITICAL"],
                "warning": counts["WARNING"],
                "info": counts["INFO"],
                "total": total
            }