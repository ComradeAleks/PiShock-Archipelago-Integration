import os
import requests
import yaml
import sys

if getattr(sys, 'frozen', False):
    current_dir = os.path.dirname(sys.executable)
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(current_dir, "config.yaml")

# Load YAML
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

#Archipelago variables:
server_port         = config["archipelago"]["room_code"]
archipelago_name    = config["archipelago"]["name"]
game                = config["archipelago"]["game"]
password            = config["archipelago"]["password"]

#PiShock variables:
pishock_name        = config["pishock"]["username"]
api_key             = config["pishock"]["api_key"]
hub_client_id       = config["pishock"]["client_id"]

#devices:
devices            = config["devices"]

#deathlink variables:
Deathlink_mode      = config["deathlink"]["activated"]
Deathlink_devices  = config["deathlink"]["devices"]

#Traps n items:
traps               = config["traps"]

#other items:
otherChecks         = config["OtherChecks"]

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

