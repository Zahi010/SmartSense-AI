# rule_engine_stub.py

from config import (
    TEMPERATURE_THRESHOLD,
    HUMIDITY_THRESHOLD,
    AIR_QUALITY_THRESHOLD,
    LIGHT_THRESHOLD
)


class RuleEngineStub:

    def evaluate(self, sensor_data):

        alerts = []

        # High Temperature
        if sensor_data["temperature"] > TEMPERATURE_THRESHOLD:
            alerts.append("🔥 High Temperature Detected")

        # High Humidity
        if sensor_data["humidity"] > HUMIDITY_THRESHOLD:
            alerts.append("💧 High Humidity Detected")

        # Poor Air Quality
        if sensor_data["air_quality"] > AIR_QUALITY_THRESHOLD:
            alerts.append("🌫 Poor Air Quality")

        # Motion Detection
        if sensor_data["motion"]:
            alerts.append("🚶 Motion Detected")

        # Low Light
        if sensor_data["light"] < LIGHT_THRESHOLD:
            alerts.append("💡 Low Light Level")

        return alerts