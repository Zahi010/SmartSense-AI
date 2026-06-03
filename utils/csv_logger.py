import csv
import os


class CSVLogger:

    def __init__(self):

        self.filename = "sensor_log.csv"

        if not os.path.exists(self.filename):

            with open(self.filename, "w", newline="") as f:

                writer = csv.writer(f)

                writer.writerow([
                    "Timestamp",
                    "Temperature",
                    "Humidity",
                    "Motion",
                    "Air Quality",
                    "Light"
                ])

    def log(self, data):

        with open(self.filename, "a", newline="") as f:

            writer = csv.writer(f)

            writer.writerow([

                data["timestamp"],
                data["temperature"],
                data["humidity"],
                data["motion"],
                data["air_quality"],
                data["light"]

            ])