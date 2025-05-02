from serial import Serial, SerialException
from serial.tools import list_ports
from RPLCD.i2c import CharLCD
import time
import os
import statistics

# ------------------- LCD Setup ------------------- #
lcd = CharLCD('PCF8574', 0x27)
lcd.clear()
lcd.write_string("Initializing...")

# ------------------- Altimeter Parser ------------------- #
def parse_altimeter(data):
    if len(data) < 8:
        return None
    altitude_raw = (data[5] << 16) | (data[6] << 8) | data[7]
    altitude = altitude_raw * 0.01
    speed_raw = (data[2] << 16) | (data[3] << 8) | data[4]
    speed = (speed_raw - 0x800000) * 0.01
    valid = data[1] & 0x01
    return {
        "altitude_m": altitude,
        "valid": bool(valid)
    }

# ------------------- CAN Message Scanner ------------------- #
def scan_for_750_messages(data):
    i = 0
    altitudes = []
    while i + 11 <= len(data):
        can_id = (data[i] << 8) | data[i + 1]
        length = data[i + 2]
        if can_id == 0x750 and length == 8:
            can_data = data[i + 3: i + 3 + 8]
            result = parse_altimeter(can_data)
            if result and result["valid"]:
                altitudes.append(result['altitude_m'])
        i += 1
    return altitudes

# ------------------- Outlier Removal via IQR ------------------- #
def remove_outliers(data):
    if len(data) < 4:
        return data
    q1 = statistics.quantiles(data, n=4)[0]
    q3 = statistics.quantiles(data, n=4)[2]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return [x for x in data if lower_bound <= x <= upper_bound]

# ------------------- Logging Setup ------------------- #
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
start_time_str = time.strftime("%Y%m%d_%H%M%S")
log_file_path = os.path.join(log_dir, f"altitude_log_{start_time_str}.txt")

log_file = open(log_file_path, mode='w')
log_file.write("timestamp\taverage_m\tvalue2\tvalue3\n")
log_file.flush()

# ------------------- Serial Port Finder ------------------- #
def find_serial_port():
    ports = list_ports.comports()
    for port in ports:
        if 'USB' in port.device or 'ttyUSB' in port.device:
            return port.device
    return None

# ------------------- Main Program ------------------- #
def main_loop():
    temp_altitudes = []
    next_log_time = time.time() + 1
    connected = False
    retries = 0
    ser = None
    no_data_counter = 0
    finished_logged = False

    while True:
        if not connected:
            port = find_serial_port()
            if port:
                try:
                    ser = Serial(port, 115200, timeout=1)
                    time.sleep(1)
                    ser.write(bytes.fromhex('AA5500000001FE'))
                    lcd.clear()
                    lcd.write_string(f"Port {port}")
                    connected = True
                    retries = 0
                    temp_altitudes.clear()
                    next_log_time = time.time() + 1
                    no_data_counter = 0
                    finished_logged = False
                except SerialException:
                    connected = False
                    ser = None
            else:
                lcd.clear()
                lcd.write_string("Waiting for USB")
                time.sleep(1)
                retries += 1
                if retries >= 300:  # 5 minutes
                    break
            continue

        try:
            response = ser.read(512)
            altitudes = scan_for_750_messages(list(response))
            temp_altitudes.extend(altitudes)

            now = time.time()
            if now >= next_log_time:
                lcd.clear()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                if temp_altitudes:
                    clean_altitudes = remove_outliers(temp_altitudes)
                    if clean_altitudes:
                        avg = sum(clean_altitudes) / len(clean_altitudes)
                        avg_str = f"{avg:.2f} m"

                        try:
                            lcd.write_string("Avg (1s):")
                            lcd.crlf()
                            lcd.write_string(avg_str)
                        except Exception as lcd_err:
                            print(f"LCD error: {lcd_err}")

                        print(f"{timestamp} - {avg_str}")
                        log_file.write(f"{timestamp}\t{avg:.6f}\t0.000000\t0.000000\n")
                        log_file.flush()
                        no_data_counter = 0
                        finished_logged = False
                    else:
                        no_data_counter += 1
                        lcd.write_string("No clean data")
                        print(f"{timestamp} - No clean data")
                else:
                    no_data_counter += 1
                    lcd.write_string("No valid data")
                    print(f"{timestamp} - No valid data")

                if no_data_counter >= 5 and not finished_logged:
                    lcd.clear()
                    lcd.write_string("Finished Process")
                    log_file.write(f"{timestamp}\tFinished Process\t\t\n")
                    log_file.flush()
                    print(f"{timestamp} - Finished Process")
                    finished_logged = True

                temp_altitudes = []
                next_log_time += 1

            time.sleep(0.05)

        except (SerialException, OSError) as e:
            print(f"Serial error: {e}")
            lcd.clear()
            lcd.write_string("USB Disconnected")
            connected = False
            if ser:
                ser.close()
                ser = None
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_loop()
    finally:
        log_file.close()
