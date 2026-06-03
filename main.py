import time
import os
import queue
import threading
from datetime import datetime
import logging
import sys
import io
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory

# Force UTF-8 encoding on Windows to prevent console emoji print crashes
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



from core.sensor_stub import SensorStub
from core.mqtt_stub import MQTTStub
from core.encryption_stub import EncryptionStub
from core.database_stub import DatabaseStub
from core.rule_engine_stub import RuleEngineStub
from core.statistics_stub import StatisticsStub
from notifications.notification_stub import NotificationStub
from dashboard.dashboard_stub import DashboardStub
from utils.alert_history import AlertHistory
from utils.csv_logger import CSVLogger
from utils.system_health import SystemHealth
from config import (
    TICK_INTERVAL,
    TEMPERATURE_THRESHOLD,
    HUMIDITY_THRESHOLD,
    AIR_QUALITY_THRESHOLD,
    LIGHT_THRESHOLD
)
from ai.ai_engine import ZScoreAnomalyDetector, TimeSeriesForecaster, HVACOptimizer, ComfortNegotiator


# ======================================
# Initialize Components
# ======================================

sensor = SensorStub()
mqtt = MQTTStub()
encryptor = EncryptionStub()
database = DatabaseStub()
rule_engine = RuleEngineStub()
notifier = NotificationStub()
dashboard = DashboardStub()
statistics = StatisticsStub()
alert_history = AlertHistory()
csv_logger = CSVLogger()
health = SystemHealth()

detector = ZScoreAnomalyDetector()
forecaster = TimeSeriesForecaster()
hvac_optimizer = HVACOptimizer(target_temp=23.0)
negotiator = ComfortNegotiator()

# Energy and Outdoor weather tracking
hvac_tracking = {
    "ROOM_101": {"cumulative_savings": 0.0},  # in Wh
    "ROOM_102": {"cumulative_savings": 0.0}
}

thresholds = {
    "temperature": TEMPERATURE_THRESHOLD,
    "humidity": HUMIDITY_THRESHOLD,
    "air_quality": AIR_QUALITY_THRESHOLD,
    "light": LIGHT_THRESHOLD
}

start_time = datetime.now()


# ======================================
# Interactive CLI Input Thread
# ======================================

input_queue = queue.Queue()
paused = False

# ======================================
# Flask Web Server Configuration
# ======================================

app = Flask(__name__, template_folder='dashboard/templates', static_folder='dashboard/user_dashboard')
app.secret_key = 'smartroom_secret_key_2024'

# Disable default flask logging to keep the console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

latest_shared_data = {}

# ======================================
# Auth Helpers
# ======================================

def login_required(role=None):
    """Check if a user is logged in. Optionally verify their role."""
    user = session.get('user')
    if not user:
        return False
    if role and user.get('role') != role:
        return False
    return True

# ======================================
# Flask Routes
# ======================================

@app.route('/')
def index_route():
    if session.get('user'):
        role = session['user'].get('role')
        if role == 'Admin':
            return redirect(url_for('admin_route'))
        return redirect(url_for('user_route'))
    return redirect(url_for('login_route'))

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if session.get('user'):
        # Already logged in — redirect to appropriate dashboard
        if session['user'].get('role') == 'Admin':
            return redirect(url_for('admin_route'))
        return redirect(url_for('user_route'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = database.lookup_user_by_credentials(username, password)
        if user:
            session['user'] = user
            database.log_audit(user['name'], 'Login', f"User logged in as {user['role']}")
            if user['role'] == 'Admin':
                return redirect(url_for('admin_route'))
            return redirect(url_for('user_route'))
        else:
            return render_template('login.html', error='Invalid username or password. Please try again.')
    
    return render_template('login.html', error=None)

@app.route('/logout')
def logout_route():
    user = session.get('user')
    if user:
        database.log_audit(user['name'], 'Logout', f"{user['name']} logged out")
    session.clear()
    return redirect(url_for('login_route'))

@app.route('/admin')
def admin_route():
    if not login_required(role='Admin'):
        # Non-admin users go to user portal; unauthenticated go to login
        if session.get('user'):
            return redirect(url_for('user_route'))
        return redirect(url_for('login_route'))
    user = session['user']
    # If no room selected yet, show the room selection screen
    selected_room = request.args.get('room', '').strip().upper()
    valid_rooms = ['ROOM_101', 'ROOM_102']
    if selected_room not in valid_rooms:
        return render_template('room_select.html', user_name=user['name'])
    return render_template('index.html', user_name=user['name'], selected_room=selected_room)


@app.route('/user')
def user_route():
    if not session.get('user'):
        return redirect(url_for('login_route'))
    user = session['user']
    # Admins who land here get sent to admin dashboard instead
    if user.get('role') == 'Admin':
        return redirect(url_for('admin_route'))
    return render_template('user.html',
                           user_name=user['name'],
                           assigned_room=user.get('assigned_room', 'ROOM_101'))

@app.route('/api/data')
def get_data_route():
    room_id = request.args.get("room_id", "ROOM_101")
    return jsonify(latest_shared_data.get(room_id, {}))

@app.route('/api/command', methods=['POST'])
def handle_web_command():
    data = request.get_json() or {}
    cmd = data.get("command")
    user = data.get("user", "Admin Operator")
    room_id = data.get("room_id", "ROOM_101")
    if cmd:
        input_queue.put((cmd, user, room_id))
    return jsonify({"status": "success", "queued": cmd})

@app.route('/api/users', methods=['GET', 'POST', 'DELETE'])
def manage_users():
    if request.method == 'GET':
        return jsonify(database.get_users())
    elif request.method == 'POST':
        data = request.get_json() or {}
        new_user = {
            "id": f"usr_{int(time.time())}",
            "name": data.get("name", "New User"),
            "role": data.get("role", "Resident"),
            "email": data.get("email", ""),
            "telegram_id": data.get("telegram_id", ""),
            "assigned_room": data.get("assigned_room", "ROOM_101")
        }
        database.add_user(new_user)
        database.log_audit("Admin", "Add User", f"Created user {new_user['name']} assigned to {new_user['assigned_room']}")
        return jsonify({"status": "success", "user": new_user})
    elif request.method == 'DELETE':
        user_id = request.args.get("id")
        if user_id:
            users = database.get_users()
            user_name = next((u["name"] for u in users if u["id"] == user_id), "Unknown")
            database.remove_user(user_id)
            database.log_audit("Admin", "Remove User", f"Deleted user {user_name} ({user_id})")
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Missing user ID"}), 400

@app.route('/api/audit-logs')
def get_audit_logs():
    return jsonify(database.get_audit_logs())

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# Start Flask in a background thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()


def console_input_thread(q):
    while True:
        try:
            cmd = input()
            if cmd:
                q.put(cmd.strip())
        except (EOFError, KeyboardInterrupt):
            break

# Start the input thread as a daemon thread
t = threading.Thread(target=console_input_thread, args=(input_queue,), daemon=True)
t.start()

print("==============================================")
print(" SMART ROOM MONITORING SYSTEM STUB")
print("==============================================")
print("System Started Successfully")
print("Commands: pause | resume | clear | trigger <fire/cold/motion/clear> | exit")
print("Press CTRL + C or type 'exit' to stop.")
print("==============================================")

try:

    while True:

        # Process any pending commands in the queue
        while not input_queue.empty():
            item = input_queue.get_nowait()
            if isinstance(item, tuple):
                cmd_raw, user, cmd_room_id = item
            else:
                cmd_raw = item
                user = "Console"
                cmd_room_id = "ROOM_101"
                
            cmd_parts = cmd_raw.lower().split()
            if not cmd_parts:
                continue
            
            action = cmd_parts[0]
            if action in ("exit", "quit"):
                raise KeyboardInterrupt
            elif action == "pause":
                paused = True
                database.log_audit(user, "Pause Loop", "Paused monitoring pipeline")
            elif action == "resume":
                paused = False
                database.log_audit(user, "Resume Loop", "Resumed monitoring pipeline")
            elif action == "clear":
                database.clear()
                alert_history.alerts.clear()
                database.log_audit(user, "Clear DB", "Cleared database records and alert history")
            elif action == "trigger":
                if len(cmd_parts) > 1:
                    sub = cmd_parts[1]
                    target_room = cmd_room_id
                    if len(cmd_parts) > 2 and cmd_parts[-1].upper().startswith("ROOM_"):
                        target_room = cmd_parts[-1].upper()
                        cmd_parts = cmd_parts[:-1]
                    
                    if sub == "fire":
                        sensor.set_override(target_room, "temperature", 42.5)
                        sensor.set_override(target_room, "air_quality", 210)
                        sensor.set_override(target_room, "motion", True)
                        database.log_audit(user, "Trigger Override", f"Fire override activated for {target_room}")
                    elif sub == "cold":
                        sensor.set_override(target_room, "temperature", 12.0)
                        database.log_audit(user, "Trigger Override", f"Cold override activated for {target_room}")
                    elif sub == "clear":
                        sensor.clear_overrides(target_room)
                        database.log_audit(user, "Clear Overrides", f"Cleared overrides for {target_room}")
                    elif len(cmd_parts) > 2:
                        val_str = cmd_parts[2]
                        try:
                            if sub == "temp":
                                sensor.set_override(target_room, "temperature", float(val_str))
                                database.log_audit(user, "Trigger Override", f"Set temp override to {val_str}°C for {target_room}")
                            elif sub == "humidity":
                                sensor.set_override(target_room, "humidity", int(val_str))
                                database.log_audit(user, "Trigger Override", f"Set humidity override to {val_str}% for {target_room}")
                            elif sub == "aqi":
                                sensor.set_override(target_room, "air_quality", int(val_str))
                                database.log_audit(user, "Trigger Override", f"Set air quality override to {val_str} AQI for {target_room}")
                            elif sub == "light":
                                sensor.set_override(target_room, "light", int(val_str))
                                database.log_audit(user, "Trigger Override", f"Set light override to {val_str} lux for {target_room}")
                            elif sub == "motion":
                                sensor.set_override(target_room, "motion", val_str in ("on", "true", "1"))
                                database.log_audit(user, "Trigger Override", f"Set motion override to {val_str} for {target_room}")
                        except ValueError:
                            pass

        if not paused:
            # Clear terminal
            os.system("cls" if os.name == "nt" else "clear")

            active_rooms = ["ROOM_101", "ROOM_102"]
            for room_id in active_rooms:
                # 1. Generate Sensor Data
                sensor_data = sensor.generate_data(room_id)

                # 2. Publish via MQTT
                mqtt.publish(f"room/{room_id}/telemetry", sensor_data)

                # 3. Subscribe to MQTT Topic
                received_data = mqtt.subscribe(f"room/{room_id}/telemetry")

                # 4. Encrypt Data
                encrypted = encryptor.encrypt(received_data)

                # 5. Store in Database
                database.insert(encrypted)

                # 6. Retrieve Latest Record for this room
                latest_record = None
                for record in reversed(database.fetch_all()):
                    dec = encryptor.decrypt(record)
                    if dec.get("room_id") == room_id:
                        latest_record = record
                        break
                
                if not latest_record:
                    continue

                # 7. Decrypt
                decrypted = encryptor.decrypt(latest_record)

                # 8. Log to CSV
                csv_logger.log(decrypted)

                # 9. Evaluate Rules
                alerts = rule_engine.evaluate(decrypted)

                # 10. Store Alert History
                if alerts:
                    alert_history.add(decrypted["room_id"], alerts)

                # 11. Calculate Statistics
                all_records = [
                    encryptor.decrypt(record)
                    for record in database.fetch_all()
                ]
                room_records = [r for r in all_records if r.get("room_id") == room_id]
                stats = statistics.calculate(room_records)

                # 11b. Evaluate AI Engine
                ai_anomalies = detector.detect(decrypted, room_records)
                ai_forecasts, ai_warnings = forecaster.forecast(room_records, thresholds)

                # 11c. Comfort Negotiation (Nash Bargaining)
                room_residents = database.get_room_residents(room_id)
                negotiation = negotiator.negotiate(
                    residents=room_residents,
                    motion_detected=decrypted.get("motion", False)
                )
                # Feed negotiated target temperature into HVAC optimizer
                hvac_optimizer.target_temp = negotiation["negotiated_temp"]

                # 11d. Evaluate HVAC & Energy Optimizer
                # Generate outdoor temperature (simulate diurnal cycle 18°C to 38°C over time)
                import math
                t_val = (datetime.now().minute * 60 + datetime.now().second) / 150.0
                outdoor_temp = 28.0 + 10.0 * math.sin(t_val)
                
                hvac_info = hvac_optimizer.optimize(decrypted, outdoor_temp)
                
                # Calculate Wh saved in this tick (TICK_INTERVAL seconds)
                base_power = 1200.0
                saved_power = max(0.0, base_power - hvac_info["power_draw"])
                wh_saved = (saved_power * TICK_INTERVAL) / 3600.0
                hvac_tracking[room_id]["cumulative_savings"] += wh_saved
                
                hvac_info["outdoor_temp"] = round(outdoor_temp, 1)
                hvac_info["cumulative_savings_kwh"] = round(hvac_tracking[room_id]["cumulative_savings"] / 1000.0, 4)

                # 12. Calculate Uptime
                uptime = datetime.now() - start_time

                # 13. Collect System Information
                mqtt_stats = mqtt.statistics()
                db_health = database.health()
                system = health.get()
                alert_summary = alert_history.summary()

                room_recent_alerts = [
                    a for a in alert_history.recent(50)
                    if a.get("room_id") == room_id
                ]

                # Populate shared data for Flask API
                latest_shared_data[room_id] = {
                    "sensor_data": decrypted,
                    "alerts": alerts,
                    "statistics": stats,
                    "uptime": str(uptime).split('.')[0],
                    "total_records": len(room_records),
                    "recent_alerts": room_recent_alerts,
                    "mqtt": mqtt_stats,
                    "database": db_health,
                    "system": system,
                    "alert_summary": alert_summary,
                    "ai_anomalies": ai_anomalies,
                    "ai_forecasts": ai_forecasts,
                    "ai_warnings": ai_warnings,
                    "hvac": hvac_info,
                    "negotiation": negotiation
                }


                # 13. Display Dashboard (ROOM_101 default on console)
                if room_id == "ROOM_101":
                    dashboard.display(
                        sensor_data=decrypted,
                        alerts=alerts,
                        statistics=stats,
                        uptime=uptime,
                        total_records=len(room_records),
                        recent_alerts=room_recent_alerts,
                        mqtt=mqtt_stats,
                        database=db_health,
                        system=system,
                        alert_summary=alert_summary,
                        ai_anomalies=ai_anomalies,
                        ai_forecasts=ai_forecasts,
                        ai_warnings=ai_warnings
                    )

                # 14. Send Notification
                if alerts:
                    notifier.send(decrypted, alerts)

        # 15. Responsive Wait for Next Cycle
        for _ in range(int(TICK_INTERVAL * 10)):
            time.sleep(0.1)
            if not input_queue.empty():
                break

except KeyboardInterrupt:

    print("\n==============================================")
    print(" Smart Room Monitoring System Stopped")
    print("==============================================")

    print(f"Total Records Stored : {database.total_records()}")

    print(f"Total Alerts Logged  : {len(alert_history.recent(1000))}")

    print("CSV Logs Saved Successfully")

    print("Goodbye!")