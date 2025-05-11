import os
import ast
import re

# Path to the .env file
env_file_path = os.path.join(os.getcwd(), ".env")
env_vars = {}
traps_raw_lines = []

with open(env_file_path, "r", encoding="utf-8") as f:
    inside_traps = False
    for line in f:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("traps"):
            inside_traps = True
            traps_raw_lines.append(stripped.split("=", 1)[1].strip())
            continue

        if inside_traps:
            traps_raw_lines.append(stripped)
            # End when we hit the last closing brace
            if stripped.endswith("}"):
                inside_traps = False
            continue

        if "=" in stripped:
            key, value = stripped.split("=", 1)
            value = re.sub(r"#.*", "", value).strip().strip("\"'")
            env_vars[key.strip()] = value

# Assign .env values
pishock_username = env_vars.get("pishock_username")
API_KEY = env_vars.get("API_KEY")
server_port = env_vars.get("server_port")
archipelago_path = env_vars.get("archipelago_path")
name = env_vars.get("Archipelago_name")

# Handle traps dictionary
traps = {}
keyword = None

if traps_raw_lines:
    raw_traps_string = "\n".join(traps_raw_lines)

    try:
        # Clean comments and trailing commas
        cleaned = re.sub(r"#.*", "", raw_traps_string)
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
        traps_dict = ast.literal_eval(cleaned)

        # Filter traps to make sure they have share_code
        for trap_name, trackers in traps_dict.items():
            valid_trackers = {
                tracker_name: tracker_data
                for tracker_name, tracker_data in trackers.items()
                if tracker_data.get("share_code") is not None
            }
            if valid_trackers:
                traps[trap_name] = valid_trackers

        keyword = next(iter(traps), None)
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing traps: {e}")
