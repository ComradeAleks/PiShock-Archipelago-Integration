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
devices             = pishock_config["devices"]

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

