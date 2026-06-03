# sensor_stub.py

import random
from datetime import datetime
from config import ROOM_ID


class SensorStub:

    def __init__(self):
        self.overrides = {}  # Format: {room_id: {metric: value}}

    def set_override(self, room_id, key, value):
        if room_id not in self.overrides:
            self.overrides[room_id] = {}
        self.overrides[room_id][key] = value

    def clear_overrides(self, room_id=None):
        if room_id is None:
            self.overrides.clear()
        elif room_id in self.overrides:
            self.overrides[room_id].clear()

    def generate_data(self, room_id=ROOM_ID):
        room_overrides = self.overrides.get(room_id, {})
        return {
            "room_id": room_id,
            "temperature": room_overrides.get("temperature", round(random.uniform(24, 40), 1)),
            "humidity": room_overrides.get("humidity", random.randint(40, 90)),
            "motion": room_overrides.get("motion", random.choice([True, False])),
            "air_quality": room_overrides.get("air_quality", random.randint(70, 220)),
            "light": room_overrides.get("light", random.randint(50, 1000)),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }