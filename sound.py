import network
import socket
from machine import Pin, ADC, PWM
import time
import urequests
import _thread

# Wi-Fi credentials
ssid = 'WIFI GRATIS'
password = 'gbu122333'

# Hardware setup
led = Pin(2, Pin.OUT)       
buzzer = PWM(Pin(15))
buzzer.freq(900)
buzzer.duty(0)  # Start with buzzer off

# Analog pin for sound sensor
sound_sensor = ADC(Pin(32))  
sound_sensor.atten(ADC.ATTN_11DB)  # 0 - 3.3V range
sound_detect = Pin(27, Pin.IN)

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        pass
    print("Connected, IP:", wlan.ifconfig()[0])

# Handle incoming violence alert
def handle_request(conn):
    request = conn.recv(1024)
    if b"/alert" in request:
        print("Violence or weapon alert received!")
        for i in range(40):
            led.on()
            buzzer.duty(1000)
            time.sleep(0.1)
            led.off()
            buzzer.duty(0)
            time.sleep(0.1)
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nOK")
    conn.close()

# Start a simple HTTP server
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        conn, _ = s.accept()
        handle_request(conn)

# Monitor sound sensor in a separate thread
def monitor_sound():
    while True:
        sound_value = sound_sensor.read()
        sound_dtc = sound_detect.value()

        # Fixed dictionary format
        data = {
            "Sound_Value": sound_value,
            "Sound_detection": sound_dtc
        }

        if sound_value > 1960:
            print("Loud sound detected:", sound_value)
            try:
                urequests.get("http://192.168.100.155:8000/sound_detected?sound=" + str(sound_value))
            except Exception as e:
                print("Failed to send sound alert:", e)

        # Call the send data function
        send_data_ubidots(data)
        time.sleep(1)

# Send data to Ubidots
def send_data_ubidots(data):
    TOKEN = "BBUS-5QUctLYAhVGEfAQxGrSSM9Zciv4g0m"  # Replace with your actual token
    device_id = "67de277cc6ae7e0b18c2d1a1"  # Replace with your actual device ID
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{device_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": TOKEN
    }

    payload = {
        "sound_level": data["Sound_Value"],
        "sound_detection": data["Sound_detection"]
    }

    try:
        response = urequests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"Data successfully sent to Ubidots! sound_level: {data["Sound_Value"]}")
        else:
            print(f"Failed to send data. Status Code: {response.status_code}")
            print("Response:", response.text)

        response.close()
        
    except Exception as e:
        print("Error sending data to Ubidots:", e)

# Run everything
connect_wifi()
_thread.start_new_thread(monitor_sound, ())  # Fixed thread syntax
start_server()
