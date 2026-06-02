# dashboard_stub.py

class DashboardStub:

    def display(
        self,
        sensor_data,
        alerts,
        statistics,
        uptime,
        total_records,
        recent_alerts,
        mqtt,
        database,
        system,
        alert_summary,
        ai_anomalies=None,
        ai_forecasts=None,
        ai_warnings=None
    ):

        print("\n" + "=" * 75)
        print("              SMART ROOM MONITORING DASHBOARD")
        print("=" * 75)

        print(f"Room ID          : {sensor_data['room_id']}")
        print(f"Timestamp        : {sensor_data['timestamp']}")
        print(f"System Uptime    : {str(uptime).split('.')[0]}")

        print("\nCURRENT SENSOR READINGS")
        print("-" * 75)

        print(f"Temperature      : {sensor_data['temperature']} °C")
        print(f"Humidity         : {sensor_data['humidity']} %")
        print(f"Motion           : {'Detected' if sensor_data['motion'] else 'Not Detected'}")
        print(f"Air Quality      : {sensor_data['air_quality']} AQI")
        print(f"Light Level      : {sensor_data['light']} lux")

        print("\nSTATISTICS")
        print("-" * 75)

        print(f"Average Temp     : {statistics['avg_temp']} °C")
        print(f"Maximum Temp     : {statistics['max_temp']} °C")
        print(f"Minimum Temp     : {statistics['min_temp']} °C")
        print(f"Average Humidity : {statistics['avg_humidity']} %")
        print(f"Average AQI      : {statistics['avg_air']}")
        print(f"Records Stored   : {total_records}")

        print("\nAI ANOMALY DETECTION")
        print("-" * 75)
        if ai_anomalies:
            for anomaly in ai_anomalies:
                print(anomaly)
        else:
            print("System Stable: No Statistical Anomalies Detected")

        print("\nAI FUTURE FORECASTS (5s ticks)")
        print("-" * 75)
        if ai_forecasts:
            print(f"Projected Temp   : {ai_forecasts.get('temperature', 'N/A')} °C (in 15s)")
            print(f"Projected AQI    : {ai_forecasts.get('air_quality', 'N/A')} AQI (in 15s)")
            if ai_warnings:
                print()
                for warning in ai_warnings:
                    print(warning)
        else:
            print("Collecting baseline data for forecasting...")

        print("\nMQTT STATUS")
        print("-" * 75)

        print(f"Messages         : {mqtt['messages']}")
        print(f"Topics           : {mqtt['topics']}")

        print("\nDATABASE STATUS")
        print("-" * 75)

        print(f"Status           : {database['status']}")
        print(f"Encrypted Records: {database['encrypted_records']}")
        print(f"Database Size    : {database['size']} bytes")

        print("\nCURRENT ALERTS")
        print("-" * 75)

        if alerts:
            for alert in alerts:
                print(f"• {alert}")
        else:
            print("No Active Alerts")

        print("\nALERT SUMMARY")
        print("-" * 75)

        print(f"Critical Alerts  : {alert_summary['critical']}")
        print(f"Warning Alerts   : {alert_summary['warning']}")
        print(f"Info Alerts      : {alert_summary['info']}")
        print(f"Total Alerts     : {alert_summary['total']}")

        print("\nRECENT ALERTS")
        print("-" * 75)

        if recent_alerts:

            for alert in recent_alerts:

                print(
                    f"{alert['time']} | "
                    f"{alert['severity']} | "
                    f"{alert['alert']}"
                )

        else:

            print("No Alerts")

        print("\nSYSTEM HEALTH")
        print("-" * 75)

        print(f"Sensor Stub      : {system['sensor']}")
        print(f"MQTT Stub        : {system['mqtt']}")
        print(f"Encryption       : {system['encryption']}")
        print(f"Database Stub    : {system['database']}")
        print(f"Rule Engine      : {system['rule_engine']}")
        print(f"Dashboard        : {system['dashboard']}")
        print(f"Python Version   : {system['python']}")
        print(f"Operating System : {system['os']}")

        print("=" * 75)