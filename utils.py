import ipaddress
import os
import re
import sys
import yaml

from urllib.parse import urlparse

# ---------------------- DEFAULT YAMLS -----------------------------------
DEFAULT_PISHOCK_CONFIG = """# This is the configuration file for the program.
# The guide is on Github under Readme
# things with # infront is just a comment

# PiShock important variables (change only the values after the colon :)
pishock:
  username: ---PishockName---
  api_key: ---API-Key---
  client_id: 12345

# PiShock device and activation profiles:
device_profiles:
  Device_1:
    device_id: 12345
    share_code: ShareCode
    
activation_profiles:
  Activation_1:
    mode: 0
    intensity: 100
    duration: 1000

# When specifying your devices in archipelago_config.yaml, 
# you combine the desired device with the desired activation profile like so:
# devices: [Device_1Activation_1, Device_2Activation_1], etc...
"""

DEFAULT_ARCHIPELAGO_CONFIG = """# This is the configuration file for the program.
# The guide is on Github under Readme
# things with # infront is just a comment

# You can optionally specify custom activation profiles here. 
# Any you specify here that have the same name as in pishock_config.yaml
# will take precedence over the ones in pishock_config.yaml.
activation_profiles:
  Activation_1:
    mode: 0
    intensity: 100
    duration: 1000

# archipelago important variables (change only the values after the colon :)
archipelago:
  server: archipelago.gg
  room_code: 12345
  name: ArchipelagoName
  password: null

# Deathlink settings
deathlink:
  activated: false
  devices: []

# Trap Link settings
trapLink:
  activated: false
  devices: []

# Archipelago Item/Trap Check Configuration
traps:
  trap-1:
    name: Item_check_name
    for_self: true
    devices: []
  trap-2:
    names:
      - Item_check_name_2
      - Item_check_name_3
    for_self: true
    devices: []

# All other items that comes from or goes to you
OtherChecks:
  activated: false
  send/receive: all                      
  devices: []
"""

def ensure_pishock_config(path):
    """
    Creates the pishock_config.yaml file with default content if it does not exist.
    """
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_PISHOCK_CONFIG)
        return False
    else:
        return True
        

def ensure_archipelago_config(path):
    """
    Creates the archipelago_config.yaml file with default content if it does not exist.
    """
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_ARCHIPELAGO_CONFIG)
        return False
    else:
        return True





# ---------------------- Varify unique keys in YAML ----------------------

class DuplicateKeyError(yaml.YAMLError):
    pass

class UniqueKeySafeLoader(yaml.SafeLoader):
    """
    Safe loader that:
      - detects duplicate keys per mapping (path like $.a.b)
      - records first occurrence + all duplicate line numbers
      - aggregates and raises once after parsing
    """

    def __init__(self, stream):
        super().__init__(stream)
        # {(path, key): {"first_line": int, "dup_lines": [int, ...]}}
        self.duplicate_keys = {}

    def construct_mapping(self, node, deep=False):
        # Determine this mapping's logical path
        current_path = getattr(node, "_ap_path", "$")

        if not isinstance(node, yaml.MappingNode):
            return super().construct_mapping(node, deep=deep)

        mapping = {}
        seen_lines = {}  # key -> first line (1-based) within THIS mapping

        # Iterate key/value pairs in this mapping
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            key_line = key_node.start_mark.line + 1

            if key in mapping:
                # Duplicate key within THIS mapping (current_path)
                entry = self.duplicate_keys.setdefault(
                    (current_path, key),
                    {"first_line": seen_lines[key], "dup_lines": []},
                )
                entry["dup_lines"].append(key_line)

                # Still construct value to keep scanning whole file
                _ = self.construct_object(value_node, deep=deep)
                continue

            # First time we see this key in THIS mapping
            seen_lines[key] = key_line

            # If the value is itself a mapping, annotate it with its child path
            if isinstance(value_node, yaml.MappingNode):
                child_path = f"{current_path}.{key}" if current_path != "$" else f"$.{key}"
                setattr(value_node, "_ap_path", child_path)

            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value

        return mapping


def safe_load_unique(stream, path):
    """
    Load YAML with SafeLoader + duplicate-key detection per mapping.
    Raises DuplicateKeyError listing all duplicates after parsing.
    """
    loader = UniqueKeySafeLoader(stream)
    try:
        data = loader.get_single_data()
    finally:
        loader.dispose()

    if loader.duplicate_keys:
        lines = [f"Duplicate keys detected in {path}:"]
        for (path, key), info in loader.duplicate_keys.items():
            first_ln = info["first_line"]
            dup_lns = ", ".join(str(n) for n in info["dup_lines"])
            lines.append(
                f"  at {path}: key {key!r} first defined on line {first_ln}, "
                f"duplicated on line(s) {dup_lns}"
            )
        raise DuplicateKeyError("\n".join(lines))

    return data
    

# ---------------------- Yaml Validation functions -------------------------    
GUID_RE = re.compile(r"^[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}$")
UPPER_HEX_RE = re.compile(r"^[0-9A-F]+$")

def require_mapping(obj, path):
    if not isinstance(obj, dict):
        raise ValueError(f"{path} must be a mapping/object.")

def require_present(d, key, path):
    if key not in d:
        raise ValueError(f"{path} missing required key '{key}'.")
    return d[key]

def require_int(val, path):
    if not isinstance(val, int):
        raise ValueError(f"{path} must be an integer.")
    return val

def require_str(val, path):
    if not isinstance(val, str) or not val:
        raise ValueError(f"{path} must be a non-empty string.")
    return val
    
def require_bool(val, path):
    if not isinstance(val, bool):
        raise ValueError(f"{path} must be a boolean.")
    return val

def require_range(n, lo, hi, path, inclusive=True):
    if inclusive:
        if not (lo <= n <= hi):
            raise ValueError(f"{path} must be in range [{lo}, {hi}].")
    else:
        if not (lo < n < hi):
            raise ValueError(f"{path} must be in range ({lo}, {hi}).")

def is_guid(s): return bool(GUID_RE.fullmatch(s))
def is_upper_hex(s): return bool(UPPER_HEX_RE.fullmatch(s))

def validate_activation_profiles_block(aprof, path):
    require_mapping(aprof, path)
    
    for name, prof in aprof.items():
        p = f"{path}.{name}"
        require_mapping(prof, p)
        
        mode = require_int(require_present(prof, "mode", p), f"{p}.mode")
        intensity = require_int(require_present(prof, "intensity", p), f"{p}.intensity")
        duration = require_int(require_present(prof, "duration", p), f"{p}.duration")
        
        require_range(mode, 0, 2, f"{p}.mode")
        require_range(intensity, 0, 100, f"{p}.intensity")
        require_range(duration, 1, 10000, f"{p}.duration")

# ---------------- Schema validation: pishock_config.yaml ----------------

def validate_pishock_config(doc):
    """
    Expected schema:

    pishock:                # required
      username: str         # required
      api_key: GUID string  # required (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
      client_id: int        # required

    device_profiles:        # optional
      <any_name>:
        device_id: int in [0, 65535]      # required
        share_code: UPPER HEX string      # required

    activation_profiles:    # optional
      <any_name>:
        mode: int in [0, 2]              # required
        intensity: int in [0, 100]       # required
        duration: int in [1, 10000]      # required
    """
    require_mapping(doc, "$")

    # --- pishock ---
    pishock = require_present(doc, "pishock", "$")
    require_mapping(pishock, "$.pishock")

    username = require_str(require_present(pishock, "username", "$.pishock"), "$.pishock.username")
    api_key  = require_str(require_present(pishock, "api_key",  "$.pishock"), "$.pishock.api_key")
    client_id = require_int(require_present(pishock, "client_id", "$.pishock"), "$.pishock.client_id")

    if not is_guid(api_key):
        raise ValueError("$.pishock.api_key must be a GUID like xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.")
        
    if "devices" in doc and ("device_profiles" in doc or "activation_profiles" in doc):
        raise ValueError(
            "Invalid configuration: 'devices' is mutually exclusive with 'device_profiles' and 'activation_profiles'. \n"
            "Use only one configuration style. (devices is deprecated)"
        )
        
    # --- devices (deprecated, optional), must be mutually exclusive with device_profiles and activation_profiles ---
    if "devices" in doc and doc["devices"] is not None:
        print("Warning: Use of devices is DEPRECATED, you should use 'device_profiles' and 'activation_profiles' insstead")
        devices = doc["devices"]
        require_mapping(devices, "$.devices")
       
        for name, device in devices.items():
            path = f"$.devices.{name}"
            require_mapping(device, path)
            
            dev_id = require_int(require_present(device, "device_id", path), f"{path}.device_id")
            require_range(dev_id, 0, 65535, f"{path}.device_id")
            
            share_code = require_str(require_present(device, "share_code", path), f"{path}.share_code")
            if not is_upper_hex(share_code):
                raise ValueError(f"{path}.share_code must be UPPERCASE hexadecimal (0-9, A-F).")
                
            mode = require_int(require_present(device, "mode", path), f"{path}.mode")
            intensity = require_int(require_present(device, "intensity", path), f"{path}.intensity")
            duration = require_int(require_present(device, "duration", path), f"{path}.duration")
            
            require_range(mode, 0, 2, f"{path}.mode")
            require_range(intensity, 0, 100, f"{path}.intensity")
            require_range(duration, 1, 10000, f"{path}.duration")
                
            

    # --- device_profiles (optional) ---
    if "device_profiles" in doc:    
        dprof = doc["device_profiles"]
        require_mapping(dprof, "$.device_profiles")

        seen_ids = set()
        seen_codes = set()

        for name, prof in dprof.items():
            path = f"$.device_profiles.{name}"
            require_mapping(prof, path)

            dev_id = require_int(require_present(prof, "device_id", path), f"{path}.device_id")
            require_range(dev_id, 0, 65535, f"{path}.device_id")

            share_code = require_str(require_present(prof, "share_code", path), f"{path}.share_code")
            if not is_upper_hex(share_code):
                raise ValueError(f"{path}.share_code must be UPPERCASE hexadecimal (0-9, A-F).")

            if dev_id in seen_ids:
                raise ValueError(f"{path}.device_id duplicates another device_id: {dev_id}")
            if share_code in seen_codes:
                raise ValueError(f"{path}.share_code duplicates another share_code: {share_code}")

            seen_ids.add(dev_id)
            seen_codes.add(share_code)

    # --- activation_profiles (optional) ---
    if "activation_profiles" in doc:
        validate_activation_profiles_block(doc["activation_profiles"], "$.activation_profiles")

    return {
        "username": username,
        "api_key": api_key,
        "client_id": client_id,
        # You can also return normalized/validated device/activation dicts if useful
    }

        
# ---------------- Schema validation: archipelago_config.yaml ----------------

    
def validate_devices(device_list, devices, path):
    print(f"Validating devices {device_list} for {path}")
    seen_device_names = set()
    seen_device_ids = set()
    for device in device_list:
        if device in seen_device_names:
            raise ValueError(f"Duplicate device {device} specified in {path}")
        seen_device_names.add(device)
        device_definition = devices.get(device, None)
        if device_definition is None:
            if devices.keys():
                raise ValueError(f"Device {device} listed in {path} is not defined: Known devices are {', '.join(devices.keys())}")
            else:
                raise ValueError(f"Device {device} listed in {path} is not defined: No devices were defined.")
        if device_definition["device_id"] in seen_device_ids:
            raise ValueError(f"Same device cannot be used for more than one activation profile in {path}")
        seen_device_ids.add(device_definition["device_id"])
    
def validate_archipelago_config(doc, pishock_devices, device_profiles, activation_profiles, *, default_server="archipelago.gg", default_room_code=38281, default_scheme="wss"):
    """
    Validates and returns a normalized dict with a computed 'archipelago_uri' like 'wss://host:port'.
    Does NOT validate device references inside lists (you said you'll handle that later).
    """
    require_mapping(doc, "$")

    # activation_profiles (optional) — validated same as pishock_config
    if "activation_profiles" in doc and doc["activation_profiles"] is not None:
        if pishock_devices:
            raise ValueError(
                "Invalid configuration: 'devices' is mutually exclusive with 'device_profiles' and 'activation_profiles'. \n"
                "Use only one configuration style. (devices is deprecated)"
            )
        validate_activation_profiles_block(doc["activation_profiles"], "$.activation_profiles")
        activation_profiles.update(doc["activation_profiles"])
        
    if device_profiles and activation_profiles:     #devices + device_profile/activation profile mutual exclusivity already verified.
        # Build all possible device combinations from device_profiles and activation profiles, one time.
        for device_key, device_value in device_profiles.items():
            for activation_key, activation_value in activation_profiles.items():
                device_name = f"{device_key}{activation_key}"
                pishock_devices[device_name] = {
                    "device_id": device_value["device_id"],
                    "share_code": device_value["share_code"],
                    "mode": activation_value["mode"],
                    "intensity": activation_value["intensity"],
                    "duration": activation_value["duration"]
                }
        

    # archipelago (required)
    arch = require_present(doc, "archipelago", "$")
    require_mapping(arch, "$.archipelago")

    name = require_str(require_present(arch, "name", "$.archipelago"), "$.archipelago.name")

    server = arch.get("server", default_server)
    # Note: they called it room_code; you said it's the port. Accept int, default 38281.
    room_code = arch.get("room_code", default_room_code)
    room_code = require_int(room_code, "$.archipelago.room_code")

    # password can be string or None
    password = arch.get("password", None)
    if password is not None and not isinstance(password, str):
        raise ValueError("$.archipelago.password must be a string or null.")

    # Validate server/URI and build normalized URI
    archipelago_uri = format_ws_uri(server, room_code, default_scheme=default_scheme)

    # deathlink (optional)
    if "deathlink" in doc and doc["deathlink"] is not None:
        dl = doc["deathlink"]
        require_mapping(dl, "$.deathlink")
        activated = require_bool(require_present(dl, "activated", "$.deathlink"), "$.deathlink.activated")
        devices = dl.get("devices", None)
        if devices is None:
            raise ValueError("$.deathlink.devices missing.")
        if not isinstance(devices, list):
            raise ValueError("$.deathlink.devices must be a list.")
        validate_devices(devices, pishock_devices, "$.deathlink.devices")
            
        

    # trapLink (optional)
    if "trapLink" in doc and doc["trapLink"] is not None:
        tl = doc["trapLink"]
        require_mapping(tl, "$.trapLink")
        activated = require_bool(require_present(tl, "activated", "$.trapLink"), "$.trapLink.activated")
        devices = tl.get("devices", None)
        if devices is None:
            raise ValueError("$.trapLink.devices missing.")
        if not isinstance(devices, list):
            raise ValueError("$.trapLink.devices must be a list.")
        validate_devices(devices, pishock_devices, "$.trapLink.devices")

    # OtherChecks (optional)
    if "OtherChecks" in doc and doc["OtherChecks"] is not None:
        oc = doc["OtherChecks"]
        require_mapping(oc, "$.OtherChecks")
        require_bool(require_present(oc, "activated", "$.OtherChecks"), "$.OtherChecks.activated")
        sr = require_str(require_present(oc, "send/receive", "$.OtherChecks"), "$.OtherChecks.send/receive").lower()
        if sr not in ("send", "receive", "all"):
            raise ValueError("$.OtherChecks.send/receive must be one of: send, receive, all.")
        devices = oc.get("devices", None)
        if devices is None:
            raise ValueError("$.OtherChecks.devices missing.")
        if not isinstance(devices, list):
            raise ValueError("$.OtherChecks.devices must be a list.")
        validate_devices(devices, pishock_devices, "$.OtherChecks.devices")

    # traps (optional) + uniqueness rules
    if "traps" in doc and doc["traps"] is not None:
        traps = doc["traps"]
        require_mapping(traps, "$.traps")

        # Track seen items per for_self value
        seen_items = {True: set(), False: set()}

        for tname, entry in traps.items():
            tp = f"$.traps.{tname}"
            require_mapping(entry, tp)

            # for_self defaults to True if not provided (as per your note)
            for_self = entry.get("for_self", True)
            if not isinstance(for_self, bool):
                raise ValueError(f"{tp}.for_self must be a boolean.")

            # Devices list present & is list (actual validation elsewhere)
            devices = entry.get("devices", None)
            if devices is None or not isinstance(devices, list):
                raise ValueError(f"{tp}.devices must be a list (can be empty).")
            validate_devices(devices, pishock_devices, f"{tp}.devices")

            # name / names rules
            has_name = "name" in entry and entry["name"] is not None
            has_names = "names" in entry and entry["names"] is not None

            if not has_name and not has_names:
                raise ValueError(f"{tp} must include 'name' or 'names' (or both).")

            items = []

            if has_name:
                n = entry["name"]
                if not isinstance(n, str) or not n:
                    raise ValueError(f"{tp}.name must be a non-empty string.")
                items.append(n)

            if has_names:
                nl = entry["names"]
                if not isinstance(nl, list) or not all(isinstance(x, str) and x for x in nl):
                    raise ValueError(f"{tp}.names must be a list of non-empty strings.")
                items.extend(nl)

            # Ensure uniqueness within the same trap entry
            if len(items) != len(set(items)):
                raise ValueError(f"{tp} has duplicate item names within the same trap definition.")

            # Ensure uniqueness across all traps with the same for_self
            overlap = set(items) & seen_items[for_self]
            if overlap:
                # Allowed only if for_self differs; here it's the same, so error
                overlap_list = ", ".join(sorted(overlap))
                raise ValueError(
                    f"{tp} has item name(s) duplicated with another trap for the same for_self={for_self}: {overlap_list}"
                )
            seen_items[for_self].update(items)

    # Build normalized, minimal result you can stash/use
    normalized = {
        "archipelago": {
            "server": server,
            "room_code": room_code,
            "name": name,
            "password": password,
            "uri": archipelago_uri,  # normalized ws/wss://host:port (IPv6 bracketed if needed)
        }
    }
    
    return normalized
    
#---------------- URI validation --------------------------
def is_ipv6_literal(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr.strip("[]"))
        return ip.version == 6
    except ValueError:
        return False

def _extract_host_and_scheme(user_addr: str):
    """Return (scheme, host_stripped). Scheme is '' if not provided."""
    s = user_addr.strip()
    # If a scheme is present, parse it; otherwise treat as raw host.
    if "://" in s:
        p = urlparse(s)
        if not p.scheme:
            raise ValueError("Invalid URI: missing scheme before '://'.")
        if p.scheme not in ("ws", "wss"):
            raise ValueError("Scheme must be 'ws' or 'wss' if specified.")
        if not p.hostname:
            raise ValueError("Invalid WebSocket URI: missing host.")
        # p.hostname strips brackets for IPv6 automatically
        return p.scheme, p.hostname
    else:
        # raw host (IPv4/IPv6/DNS), no scheme yet
        if not s:
            raise ValueError("Host cannot be empty.")
        return "", s.strip("[]")  # remove brackets if user supplied them
       
def format_ws_uri(user_addr: str, port: int, default_scheme: str = "wss") -> str:
    """
    Validate user_addr is either raw host or ws/wss URI.
    Enforce scheme ∈ {ws,wss} if present.
    Return normalized ws/wss URI with the given port.
    """
    if not isinstance(port, int) or not (0 < port <= 65535):
        raise ValueError("Port must be an integer in (0, 65535].")

    scheme, host = _extract_host_and_scheme(user_addr)

    # Use default scheme if none provided
    scheme = scheme or default_scheme
    if scheme not in ("ws", "wss"):
        raise ValueError("Scheme must be 'ws' or 'wss'.")

    # Build netloc: bracket IPv6
    if is_ipv6_literal(host):
        netloc = f"[{host}]:{port}"
    else:
        netloc = f"{host}:{port}"

    return f"{scheme}://{netloc}"
    
def pause_then_exit(code=1):
    """Always pause before exiting (good for double-click runs)."""
    try:
        input("Press Enter to exit…")
    except Exception:
        # If stdin is weird (e.g., no console), just exit
        pass
    finally:
        sys.exit(code)