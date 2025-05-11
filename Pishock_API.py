import requests
import settings

def send_vibration(tracker_name, share_code, mode, intensity, duration):
    url = "https://do.pishock.com/api/apioperate"
    payload = {
        "Username": str(settings.pishock_username),  # Replace with your PiShock username
        "Name": tracker_name,  # Use the tracker name dynamically
        "Code": share_code,  # Use the share code instead of API_KEY
        "Intensity": str(intensity),  # Intensity
        "Duration": str(duration),   # Duration
        "Apikey": settings.API_KEY,  # API_KEY required for authentication
        "Op": str(mode)  # 0 = Shock, 1 = vibration, 2 = BEEP
    }

    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        print(f"Vibration sent successfully for tracker: {tracker_name}")
    else:
        print(f"Failed to send vibration for tracker: {tracker_name}. Status code: {response.status_code}, Response: {response.text}")