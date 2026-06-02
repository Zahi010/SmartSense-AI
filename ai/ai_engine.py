# ai_engine.py

from statistics import mean, stdev


class ZScoreAnomalyDetector:

    def __init__(self, threshold=2.0, min_history=5):
        self.threshold = threshold
        self.min_history = min_history

    def detect(self, current_data, history):
        """
        Computes Z-Score for the current data against history.
        Flags values with Z-score absolute value greater than threshold.
        """
        if len(history) < self.min_history:
            return []

        anomalies = []
        metrics = ["temperature", "humidity", "air_quality"]

        for metric in metrics:
            values = [r[metric] for r in history]
            current_value = current_data[metric]

            mu = mean(values)
            sigma = stdev(values)

            if sigma > 0:
                z = (current_value - mu) / sigma
                if abs(z) > self.threshold:
                    direction = "High" if z > 0 else "Low"
                    anomalies.append(
                        f"⚠️ Anomaly: {metric.replace('_', ' ').title()} is abnormally {direction} (Z-Score: {z:.2f})"
                    )

        return anomalies


class TimeSeriesForecaster:

    def __init__(self, min_history=5, forecast_steps=3):
        self.min_history = min_history
        self.forecast_steps = forecast_steps

    def forecast(self, history, thresholds):
        """
        Performs simple linear regression over historical readings to project trends.
        Generates warnings if projected values exceed limit thresholds.
        """
        if len(history) < self.min_history:
            return {}, []

        forecasts = {}
        warnings = []
        metrics = ["temperature", "air_quality"]
        n = len(history)

        for metric in metrics:
            y = [r[metric] for r in history]
            x = list(range(n))

            sum_x = sum(x)
            sum_y = sum(y)
            sum_xx = sum(val * val for val in x)
            sum_xy = sum(x[i] * y[i] for i in range(n))

            denominator = n * sum_xx - (sum_x ** 2)
            if denominator == 0:
                continue

            m = (n * sum_xy - sum_x * sum_y) / denominator
            c = (sum_y - m * sum_x) / n

            # Project forecast value
            future_step = n - 1 + self.forecast_steps
            predicted_value = m * future_step + c
            forecasts[metric] = round(predicted_value, 2)

            limit = thresholds.get(metric)
            if limit and predicted_value > limit and m > 0:
                warnings.append(
                    f"🔮 Preemptive Alert: {metric.replace('_', ' ').title()} is rising rapidly. "
                    f"Projected to hit {predicted_value:.1f} in {self.forecast_steps * 5}s (limit: {limit})"
                )

        return forecasts, warnings


class HVACOptimizer:
    def __init__(self, target_temp=23.0, eco_band=2.0):
        self.target_temp = target_temp
        self.eco_band = eco_band

    def optimize(self, current_data, outdoor_temp):
        """
        Calculates optimal HVAC state based on indoor telemetry, occupancy, and outdoor temperature.
        """
        temp = current_data.get("temperature", 23.0)
        motion = current_data.get("motion", False)
        
        mode = "Off"
        power = 0
        advice = "Environment is comfortable. HVAC system is resting."

        # Define thresholds
        cooling_threshold = self.target_temp + (1.0 if motion else self.eco_band)
        heating_threshold = self.target_temp - (1.0 if motion else self.eco_band)

        if temp > cooling_threshold:
            # We need cooling
            if outdoor_temp < temp and outdoor_temp < self.target_temp + 1.0:
                # Outdoor air is cooler, suggest opening windows
                mode = "Off"
                power = 0
                advice = f"🍃 Outdoor air is cool ({outdoor_temp:.1f}°C). Open windows instead of running AC to save 1200W!"
            else:
                if motion:
                    mode = "Cooling (Active)"
                    power = 1200
                    advice = "❄️ Room occupied. Active cooling running to maintain comfort."
                else:
                    mode = "Cooling (Eco)"
                    power = 350
                    advice = "⏳ Room unoccupied. Running energy-saving Eco cooling mode."

        elif temp < heating_threshold:
            # We need heating
            if outdoor_temp > temp and outdoor_temp > self.target_temp - 1.0:
                # Outdoor is warmer
                mode = "Off"
                power = 0
                advice = f"☀️ Outdoor temperature is warm ({outdoor_temp:.1f}°C). Open blinds/windows to heat naturally."
            else:
                if motion:
                    mode = "Heating (Active)"
                    power = 1200
                    advice = "🔥 Room occupied. Active heating running to maintain comfort."
                else:
                    mode = "Heating (Eco)"
                    power = 350
                    advice = "⏳ Room unoccupied. Running energy-saving Eco heating mode."
        else:
            # Comfortable range
            if motion:
                advice = "😊 Room climate is optimal. Energy consumption is minimal."
            else:
                advice = "💤 Room unoccupied and climate is stable. System resting."

        return {
            "mode": mode,
            "power_draw": power,  # in Watts
            "advice": advice
        }


class ComfortNegotiator:
    """
    Implements the Nash Bargaining Solution for multi-resident thermal comfort.
    Computes a Pareto-optimal compromise temperature based on each resident's
    preferred temperature and seniority weight.
    """

    def negotiate(self, residents, motion_detected=True):
        """
        residents: list of dicts with 'name', 'preferred_temp', 'seniority_weight'
        motion_detected: if False, room is unoccupied (use average preference quietly)
        Returns a dict with full negotiation result.
        """
        if not residents:
            return {
                "negotiated_temp": 23.0,
                "present_residents": [],
                "discomfort": [],
                "fairness_index": 1.0,
                "fairness_label": "N/A",
                "status": "No residents assigned to this room."
            }

        # Room unoccupied: HVAC targets equal average of all preferences passively
        if not motion_detected:
            avg = round(sum(r["preferred_temp"] for r in residents) / len(residents), 1)
            return {
                "negotiated_temp": avg,
                "present_residents": [],
                "discomfort": [],
                "fairness_index": 1.0,
                "fairness_label": "Unoccupied",
                "status": f"💤 Room unoccupied. HVAC holding at average preference ({avg}°C)."
            }

        # Nash Bargaining: weighted average of preferred temperatures
        total_weight = sum(r.get("seniority_weight", 1.0) for r in residents)
        if total_weight == 0:
            total_weight = len(residents)

        negotiated_temp = sum(
            r["preferred_temp"] * r.get("seniority_weight", 1.0)
            for r in residents
        ) / total_weight
        negotiated_temp = round(negotiated_temp, 1)

        # Per-person discomfort analysis
        discomfort = []
        for r in residents:
            delta = round(negotiated_temp - r["preferred_temp"], 1)
            direction = (f"+{delta}°C warmer than preferred" if delta > 0
                         else f"{delta}°C cooler than preferred" if delta < 0
                         else "Exactly at preferred")
            discomfort.append({
                "name": r["name"],
                "preferred": r["preferred_temp"],
                "weight": round(r.get("seniority_weight", 1.0), 2),
                "delta": delta,
                "direction": direction,
                "comfort_loss": round(abs(delta), 1)
            })

        # Jain's Fairness Index: J = (Σxᵢ)² / (n · Σxᵢ²)
        losses = [d["comfort_loss"] for d in discomfort]
        n = len(losses)
        sum_x  = sum(losses)
        sum_x2 = sum(l ** 2 for l in losses)

        if sum_x2 == 0:
            fairness_index = 1.0   # Everyone perfectly comfortable
        elif n == 1:
            fairness_index = 1.0   # Single resident always fair
        else:
            fairness_index = round((sum_x ** 2) / (n * sum_x2), 3)

        if fairness_index >= 0.95:
            fairness_label = "⚖️ Near-Perfect"
        elif fairness_index >= 0.80:
            fairness_label = "✅ Balanced"
        elif fairness_index >= 0.60:
            fairness_label = "⚠️ Moderate Bias"
        else:
            fairness_label = "🔴 High Conflict"

        names = " & ".join(r["name"] for r in residents)
        if fairness_index >= 0.80:
            status = (f"✅ Equitable compromise at {negotiated_temp}°C for {names}. "
                      f"Discomfort is shared fairly.")
        else:
            worst = max(discomfort, key=lambda d: d["comfort_loss"])
            status = (f"⚠️ Compromise at {negotiated_temp}°C. {worst['name']} bears more "
                      f"discomfort ({worst['direction']}). Consider adjusting weights.")

        return {
            "negotiated_temp": negotiated_temp,
            "present_residents": [r["name"] for r in residents],
            "discomfort": discomfort,
            "fairness_index": fairness_index,
            "fairness_label": fairness_label,
            "status": status
        }


