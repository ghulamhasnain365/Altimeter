# Altimeter
Altimeter development which includes acquisition of altitude data , display on the I2C screen and stored in the log file.

Altimeter Logger Project Documentation
________________________________________
1. Introduction
This project involves building a robust data logging system for an altimeter sensor using a Raspberry Pi 4. The altimeter communicates over USB and provides CAN messages. The goal is to continuously log altitude readings, display real-time information on an LCD, and handle connection interruptions.
2. System Overview
•	Device: Raspberry Pi 4
•	Sensor: USB Altimeter (CAN data over serial)
•	Interface: Serial Communication via USB
•	Display: I2C LCD
•	Output: Altitude logs in .txt files, updated every second
3. Hardware Requirements
•	Raspberry Pi 4
•	USB Altimeter Device
•	I2C 16x2 LCD Display
•	USB Cable
•	MicroSD Card (with Raspberry Pi OS)
4. Software Requirements
•	Python 3.x
•	pyserial
•	RPLCD
•	python3-systemd (for service file support)
5. Directory Structure
/home/altimeter/Python/
    ├── Altimeter_logger.py
    ├── logs/
    │   └── altitude_log_YYYYMMDD_HHMMSS.txt
    └── altimeter_logger.service
6. Detailed Module Descriptions
LCD Setup
Initializes a 16x2 character LCD using I2C (address 0x27). Displays system messages such as status, altitude average, USB disconnection, and process completion.
Altimeter Data Parsing
Reads 8-byte CAN messages (ID: 0x750) and extracts altitude and validity. Uses bitwise operations to decode data.
CAN Message Processing
Scans incoming serial data for CAN messages. Filters only 0x750 messages with valid altitude data.
Outlier Removal
Applies the Interquartile Range (IQR) method to filter out abnormal readings before calculating average altitude.
Logging System
Creates a log file with the naming format altitude_log_YYYYMMDD_HHMMSS.txt in logs/. Every second, writes the timestamp and average altitude. The flush() method ensures immediate disk writing for crash resilience.
USB Connection Handling
Automatically detects available USB ports. If disconnected, attempts reconnection for up to 5 minutes. Can recover if device is plugged into a different USB port.
Sensor Timeout Handling
If no valid sensor readings are received for 5 consecutive seconds, logs and displays "Finished Process".
Systemd Auto-Start Configuration
A systemd service is used to ensure the script runs at boot:
altimeter_logger.service
[Unit]
Description=Altimeter Logger
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 /home/altimeter/Python/Altimeter_logger.py
WorkingDirectory=/home/altimeter/Python
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
Enable with:
sudo systemctl enable altimeter_logger.service
7. Usage Instructions
1.	Connect the USB Altimeter and LCD.
2.	Power on the Raspberry Pi.
3.	The script starts automatically via systemd.
4.	Monitor the LCD for real-time altitude.
5.	Logs are saved in logs/.
8. Troubleshooting
Issue	Solution
No USB detected	Replug or try another port. Check cable.
LCD doesn't display text	Check wiring and I2C address (0x27).
Log file not updating	Check disk space and permissions.
"Finished Process" appears	Sensor has stopped sending data. Check power.
9. Future Improvements
•	Add graphical logging (e.g., charts).
•	Enable remote monitoring via web server.
•	Integrate battery status for mobile logging.
10. Appendix
Example Log File
timestamp    average_m    value2    value3
2025-04-29 11:01:12    78.341000    0.000000    0.000000
2025-04-29 11:01:13    78.411000    0.000000    0.000000
... (updated every second)
________________________________________


