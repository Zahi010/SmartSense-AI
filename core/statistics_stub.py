from statistics import mean


class StatisticsStub:

    def calculate(self, records):

        if not records:
            return None

        temps = [r["temperature"] for r in records]
        humidity = [r["humidity"] for r in records]
        air = [r["air_quality"] for r in records]

        return {

            "avg_temp": round(mean(temps), 2),
            "max_temp": max(temps),
            "min_temp": min(temps),

            "avg_humidity": round(mean(humidity), 2),

            "avg_air": round(mean(air), 2),

            "total_records": len(records)

        }