import platform
import time


class SystemHealth:

    def __init__(self):

        self.start = time.time()

    def get(self):

        uptime = int(time.time() - self.start)

        return {

            "sensor": "ONLINE",
            "mqtt": "CONNECTED",
            "database": "CONNECTED",
            "encryption": "ACTIVE",
            "rule_engine": "RUNNING",
            "dashboard": "ACTIVE",

            "python": platform.python_version(),
            "os": platform.system(),

            "uptime": uptime

        }