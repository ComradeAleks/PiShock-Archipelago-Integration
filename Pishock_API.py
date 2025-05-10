import requests
import settings

def send_vibration(mode, intensity, duration):
    url = "https://do.pishock.com/api/apioperate"
    payload = {
        "Username": str(settings.pishock_username),  # Replace with your PiShock username
        "Name": "Automatic shock",  # Replace with your device name (or just write whatever you want)
        "Code": settings.SHARE_CODE,
        "Intensity": str(intensity),  # Intensity as a string
        "Duration": str(duration),   # Duration as a string
        "Apikey": settings.API_KEY,
        "Op": str(mode)  # 0 = Shock, 1 = vibration, 2 = BEEP
    }

    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        print("sent successfully!")
    else:
        print(f"Failed to send vibration. Status code: {response.status_code}, Response: {response.text}")