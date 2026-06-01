<div align="center">

# 🏠 SmartSense AI

### Real-time IoT Room Monitoring System with AI-Powered Intelligence

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web%20Dashboard-black?logo=flask)](https://flask.palletsprojects.com)
[![MQTT](https://img.shields.io/badge/MQTT-IoT%20Protocol-orange)](https://mqtt.org)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI%20Alerts-purple?logo=google)](https://aistudio.google.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

*A fully-featured smart room monitoring system that combines IoT sensor pipelines, AI anomaly detection, predictive forecasting, HVAC optimization, and multi-resident comfort negotiation — all with real-time Telegram alerts and a live web dashboard.*

</div>

---

## 📖 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [AI Engine](#-ai-engine)
- [Alert System](#-alert-system)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Setup & Installation](#️-setup--installation)
- [Running the System](#-running-the-system)
- [Dashboard](#-web-dashboard)
- [Resume Entry](#-resume-entry)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📡 **Live Sensor Monitoring** | Reads Temperature, Humidity, Air Quality (AQI), Motion, and Light Level every 5 seconds |
| 🤖 **Z-Score Anomaly Detection** | Statistically flags abnormal sensor readings using Z-Score analysis |
| 🔮 **Predictive Forecasting** | Linear regression projects Temperature & AQI values 15 seconds into the future |
| 🌡️ **HVAC Optimizer** | Recommends optimal AC/heating mode based on occupancy and outdoor temperature |
| 🤝 **Comfort Negotiator** | Nash Bargaining Solution for fair multi-resident temperature compromise |
| 🔔 **Smart Rule Engine** | CRITICAL / WARNING / INFO alert tiers based on configurable thresholds |
| 💬 **Telegram Alerts** | Instant push notifications with AI-generated natural language summaries (Gemini) |
| 🌐 **Live Web Dashboard** | Flask dashboard showing real-time readings, AI forecasts, and alert history |
| 🔒 **Encrypted Storage** | All sensor records encrypted with Fernet before saving to SQLite |
| 📨 **MQTT Pipeline** | Publish/subscribe telemetry messaging for IoT-grade data flow |
| 📊 **CSV Logging** | Persistent CSV export of all sensor readings for offline analysis |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SmartSense AI                          │
│                                                             │
│   [Sensor Stub]  ──►  [MQTT Broker]  ──►  [Rule Engine]    │
│        │                                        │           │
│        ▼                                        ▼           │
│   [Encryption]  ──►  [SQLite DB]        [Alert History]    │
│        │                                        │           │
│        ▼                                        ▼           │
│   [AI Engine]                          [Notification Hub]  │
│   ├── Z-Score Anomaly Detector          ├── Telegram Bot   │
│   ├── Linear Regression Forecaster      └── Gemini AI      │
│   ├── HVAC Optimizer                                        │
│   └── Comfort Negotiator                                   │
│                                                             │
│   [Flask Dashboard]  ◄─────────────────────────────────    │
└─────────────────────────────────────────────────────────────┘
```

Every 5 seconds (`TICK_INTERVAL`), the system:
1. Reads simulated sensor data
2. Publishes via MQTT → subscribes and receives
3. Encrypts and stores in SQLite
4. Runs the rule engine for threshold checks
5. Runs the AI engine for anomaly + forecasting
6. Sends Telegram + Gemini AI summary if alerts fire
7. Updates the live Flask dashboard

---

## 🤖 AI Engine

The AI engine (`ai_engine.py`) contains four intelligent modules:

### 1. Z-Score Anomaly Detector
Computes the statistical Z-Score of current sensor readings against historical data. Any reading that deviates beyond 2 standard deviations is flagged as an anomaly.

```
Z = (current_value - mean) / std_deviation
If |Z| > 2.0  →  Anomaly Detected
```

### 2. Time Series Forecaster
Uses **linear regression** (from scratch, no external ML libraries) to project temperature and AQI values 15 seconds ahead. Triggers preemptive alerts if the predicted value will exceed threshold limits.

```
y = mx + c  (fitted on historical readings)
Predicts value at  t + 3 ticks (15 seconds ahead)
```

### 3. HVAC Optimizer
Recommends the optimal heating/cooling state based on:
- Current indoor temperature vs. target (23°C)
- Motion detection (occupied vs. unoccupied)
- Simulated outdoor temperature

Switches between `Active`, `Eco`, and `Off` modes — and suggests opening windows when outdoor air can naturally cool/heat the room, saving up to 1200W.

### 4. Comfort Negotiator *(Nash Bargaining)*
For multi-resident rooms, computes a Pareto-optimal compromise temperature using the **Nash Bargaining Solution** with seniority-weighted preferences. Calculates **Jain's Fairness Index** to report how equitably discomfort is distributed among residents.

```
Negotiated Temp = Σ(preferred_temp × weight) / Σ(weight)
Fairness Index  = (Σxᵢ)² / (n · Σxᵢ²)   [Jain's Formula]
```

---

## 🔔 Alert System

Alerts are classified into three severity levels:

| Severity | Emoji | Condition |
|---|---|---|
| 🔴 CRITICAL | 🔥 High Temperature | Temp > 35°C |
| 🔴 CRITICAL | ❄️ Cold Alert | Temp < 18°C |
| 🟡 WARNING | 💧 High Humidity | Humidity > 80% |
| 🟡 WARNING | 🌫 Poor Air Quality | AQI > 150 |
| 🟡 WARNING | 🔮 Preemptive Alert | Forecasted breach |
| 🔵 INFO | 🚶 Motion Detected | Motion sensor active |
| 🔵 INFO | 💡 Low Light | Light < 200 lux |

When an alert fires, a **Telegram notification** is sent with an optional **AI-generated summary** via Google Gemini API.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.13 | Core runtime |
| Web Framework | Flask | Live dashboard server |
| IoT Protocol | MQTT (stubbed) | Publish/subscribe telemetry |
| AI / ML | Custom Python (no ML libs) | Z-Score, linear regression |
| Generative AI | Google Gemini API | Natural language alert summaries |
| Notifications | Telegram Bot API | Push alerts |
| Database | SQLite | Persistent encrypted storage |
| Encryption | Fernet (cryptography) | AES-128 record encryption |
| Logging | CSV + JSONL | Offline data export |

> **Note:** All ML/AI algorithms (Z-Score anomaly detection, linear regression forecaster, Nash Bargaining) are implemented from scratch using Python's built-in `statistics` module — no NumPy, Pandas, or scikit-learn required.

---

## 📁 Project Structure

```
smartsense-ai/
│
├── main.py                 # 🎛️  Main orchestrator loop + Flask app
├── ai_engine.py            # 🤖  Z-Score detector, forecaster, HVAC, Comfort Negotiator
├── rule_engine_stub.py     # 📋  Threshold-based alert rules
├── notification_stub.py    # 📲  Telegram Bot + Gemini AI integration
├── dashboard_stub.py       # 🌐  Flask dashboard renderer
├── database_stub.py        # 🗄️  Encrypted SQLite read/write
├── sensor_stub.py          # 📡  Simulated IoT sensor data generator
├── mqtt_stub.py            # 📨  MQTT publish/subscribe simulation
├── encryption_stub.py      # 🔒  Fernet encryption layer
├── alert_history.py        # 📜  In-memory alert log
├── statistics_stub.py      # 📊  Running stats (avg, min, max)
├── csv_logger.py           # 📁  CSV export of sensor readings
├── system_health.py        # 💚  System component status tracker
│
├── templates/              # HTML templates for Flask dashboard
│   ├── index.html          # Main dashboard
│   ├── login.html          # Login page
│   ├── room_select.html    # Room selector
│   └── user.html           # User dashboard view
│
├── config.example.py       # ⚙️  Credentials template (copy to config.py)
├── requirements.txt        # 📦  Python dependencies
└── .gitignore              # 🚫  Excludes secrets, DB, logs
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- A Telegram Bot token (from [@BotFather](https://t.me/BotFather))
- A Google Gemini API key (from [AI Studio](https://aistudio.google.com/app/apikey)) *(optional — alerts work without it)*

### 1. Clone the repository
```bash
git clone https://github.com/Zahi010/SmartSense-AI.git
cd SmartSense-AI
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure credentials
```bash
cp config.example.py config.py
```

Edit `config.py`:
```python
TELEGRAM_BOT_TOKEN = "your-bot-token"
TELEGRAM_CHAT_ID   = "your-chat-id"
GEMINI_API_KEY     = "AIzaSy..."      # Optional
ROOM_ID            = "ROOM_101"
TICK_INTERVAL      = 5                # Seconds between readings
```

---

## ▶️ Running the System

```bash
python main.py
```

The system will:
- Start the Flask dashboard at **http://localhost:5000**
- Begin reading sensors every 5 seconds
- Send Telegram alerts when thresholds are breached
- Display a live console dashboard with all metrics

### Console Commands (while running)

| Command | Action |
|---|---|
| `pause` | Pause sensor loop |
| `resume` | Resume sensor loop |
| `clear` | Clear alert history |
| `trigger fire` | Manually trigger a fire scenario |
| `trigger cold` | Manually trigger a cold scenario |
| `trigger motion` | Manually trigger motion detection |
| `trigger clear` | Reset to normal readings |
| `exit` | Stop the system |

---

## 🌐 Web Dashboard

The Flask dashboard at `http://localhost:5000` displays:

- **Live sensor readings** — refreshed every 5 seconds
- **Running statistics** — average, min, max across all records
- **AI anomaly status** — whether current readings are statistically normal
- **15-second forecasts** — projected temperature and AQI
- **HVAC recommendation** — optimal mode and power draw
- **Comfort negotiation** — per-resident discomfort and fairness score
- **Recent alert log** — last 5 alerts with severity and timestamp
- **System health** — status of all components (MQTT, DB, Encryption, etc.)

---

## 📄 Resume Entry

**SmartSense AI** | [github.com/Zahi010/SmartSense-AI](https://github.com/Zahi010/SmartSense-AI)
`Python` `Flask` `MQTT` `SQLite` `Google Gemini AI` `Telegram Bot API`

- Built a real-time IoT monitoring system ingesting environmental sensor data (temperature, humidity, AQI, motion, light) via MQTT and storing encrypted records in SQLite
- Implemented a **Z-Score anomaly detector** and **linear regression time series forecaster** from scratch (no ML libraries) to predict sensor breaches 15 seconds ahead
- Designed an **HVAC Optimizer** and **Nash Bargaining Comfort Negotiator** (Jain's Fairness Index) for intelligent, multi-resident climate control
- Integrated **Google Gemini API** for AI-generated alert summaries delivered via **Telegram Bot**
- Built a live **Flask web dashboard** with real-time metrics, AI forecasts, and alert history

---

## 📝 License

MIT License — feel free to use, fork, and build on this project.

---

<div align="center">
Made with ❤️ by <a href="https://github.com/Zahi010">Zahi010</a>
</div>
