# notification_stub.py

from datetime import datetime
import json
import time
import urllib.request
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import SLACK_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY


class NotificationStub:

    def __init__(self):
        self._last_gemini_call = 0  # Unix timestamp of last Gemini API call
        self._gemini_cooldown = 60  # Only call Gemini once every 60 seconds

    def send(self, sensor_data, alerts):
        room_id = sensor_data["room_id"]

        print("\n" + "=" * 50)
        print("        SMART ROOM ALERT")
        print("=" * 50)

        print(f"Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Room ID   : {room_id}")

        print("\nAlerts:")

        for alert in alerts:
            print(f" - {alert}")

        print("\nStatus : Notification Sent Successfully")

        print("=" * 50)

        # Get AI insights if key is configured
        ai_summary = self._get_gemini_summary(sensor_data, alerts)
        if ai_summary:
            print(f"\nAI Insights:\n{ai_summary}\n")
            print("=" * 50)

        if SLACK_WEBHOOK_URL:
            self._send_slack(room_id, alerts, ai_summary)
            
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            self._send_telegram(room_id, alerts, ai_summary)

    def _get_gemini_summary(self, sensor_data, alerts):
        if not GEMINI_API_KEY:
            return ""

        # Rate limit: only call Gemini once per cooldown period
        now = time.time()
        if now - self._last_gemini_call < self._gemini_cooldown:
            return ""
        self._last_gemini_call = now

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"
        
        prompt = (
            "You are an AI monitoring a smart room. Analyze these readings and active alerts. "
            "Generate a friendly, concise 2-sentence summary explaining the situation and suggesting a quick solution. "
            "Do not use markdown formatting in your response.\n"
            f"Readings: Temp={sensor_data['temperature']}°C, Humidity={sensor_data['humidity']}%, "
            f"Motion={'Detected' if sensor_data['motion'] else 'None'}, Air Quality={sensor_data['air_quality']} AQI, "
            f"Light={sensor_data['light']} lux.\n"
            f"Active Alerts: {', '.join(alerts)}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                summary = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return summary
        except Exception as e:
            print(f"[AI Exception] Failed to get Gemini summary: {e}")
            return ""

    def _send_slack(self, room_id, alerts, ai_summary):
        title = f"🚨 *Smart Room Alert [{room_id}]*"
        alert_list = "\n".join(f"• {alert}" for alert in alerts)
        
        content = f"{title}\n"
        if ai_summary:
            content += f"\n*AI Insights:*\n_{ai_summary}_\n"
        content += f"\n*Alert Details:*\n{alert_list}"

        payload = {
            "text": content
        }

        try:
            req = urllib.request.Request(
                SLACK_WEBHOOK_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "SmartRoomMonitor"
                }
            )
            with urllib.request.urlopen(req, timeout=3):
                pass
        except Exception as e:
            print(f"[Slack Exception] Failed to send webhook: {e}")

    def _send_telegram(self, room_id, alerts, ai_summary):
        title = f"🚨 *Smart Room Alert [{room_id}]*"
        alert_list = "\n".join(f"• {alert}" for alert in alerts)

        content = f"{title}\n"
        if ai_summary:
            content += f"\n*AI Insights:*\n{ai_summary}\n"
        content += f"\n*Alert Details:*\n{alert_list}"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": content,
            "parse_mode": "Markdown"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "SmartRoomMonitor"
                }
            )
            with urllib.request.urlopen(req, timeout=3):
                pass
        except Exception as e:
            print(f"[Telegram Exception] Failed to send message: {e}")

