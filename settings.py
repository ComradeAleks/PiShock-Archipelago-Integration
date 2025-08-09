import os
import requests
import yaml
import sys

if getattr(sys, 'frozen', False):
    current_dir = os.path.dirname(sys.executable)
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) > 1:
    archipelago_config_path = sys.argv[1]
else:
    archipelago_config_path = os.path.join(current_dir, "archipelago_config.yaml")
    
pishock_config_path = os.path.join(current_dir, "pishock_config.yaml")

# Load YAML
with open(pishock_config_path, 'r') as file:
    pishock_config = yaml.safe_load(file)
    
with open(archipelago_config_path, 'r') as file:
    archipelago_config = yaml.safe_load(file)
    
## PiShock configuration data
#PiShock variables:
pishock_name        = pishock_config["pishock"]["username"]
api_key             = pishock_config["pishock"]["api_key"]
hub_client_id       = pishock_config["pishock"]["client_id"]

#devices:
devices             = pishock_config.get("devices", {})
device_profiles     = pishock_config.get("device_profiles", {})
activation_profiles = pishock_config.get("activation_profiles", {})
ap_activations      = archipelago_config.get("activation_profiles", {})

activation_profiles.update(ap_activations)
if not devices and device_profiles and activation_profiles:
    # Build all possible device combinations from device_profiles and activation profiles, one time.
    for device_key, device_value in device_profiles.items():
        for activation_key, activation_value in activation_profiles.items():
            device_name = f"{device_key}{activation_key}"
            devices[device_name] = {
                "device_id": device_value["device_id"],
                "share_code": device_value["share_code"],
                "mode": activation_value["mode"],
                "intensity": activation_value["intensity"],
                "duration": activation_value["duration"]
            }



## Archipelago configuration data
#Archipelago variables:
server_port         = archipelago_config["archipelago"]["room_code"]
archipelago_name    = archipelago_config["archipelago"]["name"]
game                = archipelago_config["archipelago"]["game"]
password            = archipelago_config["archipelago"].get("password", None)

#deathlink variables:
DeathLink           = archipelago_config.get("deathlink", {"activated": False, "devices": []})
Deathlink_mode      = DeathLink.get("activated", False)
Deathlink_devices   = DeathLink.get("devices", [])

#trapLink variables:
TrapLink            = archipelago_config.get("trapLink", {"activated": False, "devices": []})
trapLink_mode       = TrapLink.get("activated", False)
trapLink_devices    = TrapLink.get("devices", [])

#Traps n items:
traps               = archipelago_config.get("traps", {})

#other items:
otherChecks         = archipelago_config.get("OtherChecks", {"activated": False, "send/receive": "all", "devices": []})

def fetch_user_id() -> str:
    """
    Fetches and returns your numeric PiShock UserID by validating
    the API key and username via the Auth/GetUserIfAPIKeyValid endpoint.
    """
    url = (
        "https://auth.pishock.com/Auth/GetUserIfAPIKeyValid"
        f"?apikey={api_key}"
        f"&username={pishock_name}"
    )
    resp = requests.get(url)
    resp.raise_for_status()  # will raise an HTTPError for 4xx/5xx

    data = resp.json()
    # The JSON payload should include something like {"UserId":"123456", ...}
    user_id = data.get("UserId") or data.get("userId") or data.get("ID")
    if not user_id:
        raise ValueError(f"Unexpected response format: {data!r}")
    return str(user_id)

USERID = fetch_user_id()

