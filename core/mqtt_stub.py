# mqtt_stub.py

import json
from datetime import datetime


class MQTTStub:

    def __init__(self):
        self.messages = []
        self.total_messages = 0

    def publish(self, topic, payload):

        message = {
            "topic": topic,
            "payload": payload,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        self.messages.append(message)
        self.total_messages += 1

        payload_size = len(json.dumps(payload).encode("utf-8"))

        print("\n========== MQTT BROKER ==========")
        print(f"Action       : PUBLISH")
        print(f"Topic        : {topic}")
        print(f"QoS          : 1")
        print(f"Payload Size : {payload_size} bytes")
        print(f"Status       : Delivered")
        print("=================================")

    def subscribe(self, topic):

        for message in reversed(self.messages):

            if message["topic"] == topic:

                print("\n========== MQTT BROKER ==========")
                print(f"Action       : SUBSCRIBE")
                print(f"Topic        : {topic}")
                print(f"Received At  : {message['timestamp']}")
                print("Status       : Success")
                print("=================================")

                return message["payload"]

        return None

    def statistics(self):

        return {
            "messages": self.total_messages,
            "topics": len(set(msg["topic"] for msg in self.messages))
        }