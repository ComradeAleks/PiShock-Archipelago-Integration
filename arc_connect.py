import gzip
import json
import uuid
import json
import asyncio
import websockets
import ItemChecks
import Pishock_API
import settings
import ast

serverport = str(settings.server_port)
SERVER_URI     = "wss://archipelago.gg:" + serverport
SLOT_NAME      = settings.name
GAME           = settings.Game
ITEMS_HANDLING = 0b001
SLOT_DATA      = False

if settings.Password != "None":
    PASSWORD = settings.Password
else:
    PASSWORD = ""
if settings.Deathlink == "True":
    TAGS = ["DeathLink"]
elif settings.Deathlink == "False":
    TAGS = []


D_Tracker_names = settings.Deathlink_Tracker_name
D_mode = settings.Deathlink_mode
D_intesity = settings.Deathlink_intensity
D_duration = settings.Deathlink_duration
D_Share_Codes = settings.DeathLink_Share_code
D_Share_Codes = ast.literal_eval(D_Share_Codes)

async def archipelago_client():
    name_map = {}
    location_map = {}
    seen_locations = set()

    async with websockets.connect(SERVER_URI, max_size=None) as ws:
        # 1) Initial RoomInfo
        raw = await ws.recv()
        packet = json.loads(raw)
        room_info = next(
            (cmd for cmd in (packet if isinstance(packet, list) else [packet]) if cmd.get("cmd") == "RoomInfo"),
            None
        )
        if room_info is None:
            raise RuntimeError("Did not receive RoomInfo from server")
        #print("RoomInfo:", room_info)

        # 2) Build dynamic games list for DataPackage
        games_field = room_info.get("games") or room_info.get("Games")
        server_games = list(games_field.keys()) if isinstance(games_field, dict) else games_field or []

        # 3) Request the DataPackage for those games or just do the whole shlabang if that dont work for some reason
        dp_version = room_info.get("datapackage_version") or room_info.get("data_package_version") or 1
        dp_req = {"cmd": "GetDataPackage", "version": dp_version}
        if server_games:
            dp_req["games"] = server_games
            print(f"Fetching DataPackage for games: {server_games}")
        else:
            print("Fetching full DataPackage (all games)")
        await ws.send(json.dumps([dp_req]))

        # 4) Process DataPackage to populate name_map and location_map
        while True:
            frame = await ws.recv()
            if isinstance(frame, (bytes, bytearray)):
                try:
                    data = gzip.decompress(frame).decode()
                    pkg = json.loads(data).get('games', {}).get(GAME, {})
                except Exception:
                    continue
            else:
                packet = json.loads(frame)
                pkg = None
                for cmd in packet:
                    if cmd.get('cmd') == 'DataPackage':
                        pkg = cmd['data'].get('games', {}).get(GAME, {})
                        break
                if pkg is None:
                    continue

            # Invert mappings from DataPackage
            item_map = pkg.get('item_name_to_id', {})
            name_map = {item_id: name for name, item_id in item_map.items()}
            loc_map = pkg.get('location_name_to_id', {})
            location_map = {loc_id: name for name, loc_id in loc_map.items()}
            print(f"Loaded {len(name_map)} items and {len(location_map)} locations for {GAME}")
            break

        # 5) Send Connect
        await ws.send(json.dumps([{
            "cmd":            "Connect",
            "name":           SLOT_NAME,
            "password":       PASSWORD,
            "game":           GAME,
            "uuid":           str(uuid.uuid4()),
            "version":        {"major": 0, "minor": 6, "build": 1, "class": "Version"},
            "items_handling": ITEMS_HANDLING,
            "tags":           TAGS,
            "slot_data":      SLOT_DATA
        }]))
        print("Connecting to server...")

        # 6) Connected confirmation
        connected = json.loads(await ws.recv())
        #print("Connected:", connected)
        print("… now listening for RoomUpdate and ReceivedItems …")
        
        MY_SLOT_ID = get_my_slot(connected, SLOT_NAME)

        # 7) Main event loop
        while True:
            frame = await ws.recv()

            # Handle binary DataPackage updates
            if isinstance(frame, (bytes, bytearray)):
                continue
            packet = json.loads(frame)
            for cmd in packet:
                c = cmd.get("cmd")
                
                # when you get an item
                if c == "PrintJSON" and cmd.get("type") == "ItemSend":
                    # 1) checking if the item belongs to you
                    if cmd.get("receiving") != MY_SLOT_ID:
                        continue

                    # 2) gets the item_id, from the JSON text field
                    for entry in cmd.get("data", []):
                        if entry.get("type") == "item_id":
                            if entry.get("player") != MY_SLOT_ID:
                                break

                            # self pickup and item confirmed:
                            item_id   = int(entry["text"])
                            item_name = name_map.get(item_id, "<unknown>")
                            print(f"Recieved item: {item_name} (ID {item_id})")

                            # shocking time
                            ItemChecks.check_for_traps(item_name)
                            break

                # Auto-checking locations
                elif c == "RoomUpdate":
                    new_locs = [loc for loc in cmd.get("checked_locations", []) if loc not in seen_locations]
                    for loc in new_locs:
                        seen_locations.add(loc)
                        await ws.send(json.dumps([{"cmd": "CheckLocation", "location": loc}]))

                # DeathLink
#                elif c == "DeathLink":
#                    print(f"DeathLink from {cmd['source']!r}: {cmd['cause']!r}")
#                    Pishock_API.send_vibration(D_Tracker_names, D_Share_Codes, D_mode, D_intesity, D_duration)
                elif c == "Bounced" or c == "DeathLink":
                    d = cmd.get("data", {})
                    print(f"DeathLink from {d.get('source')!r} because of {d.get('cause')!r}")
                    ItemChecks.send_shock(D_Tracker_names, D_Share_Codes, D_mode, D_intesity, D_duration)
                else:
                    #print(f"Other `{c}`: {cmd!r}")
                    pass


#use the connect payload to find the player slot aka your slot, and then return it for the other thingimajig
def get_my_slot(connect_payload, my_name):
    if not isinstance(connect_payload, list):
        return None

    for entry in connect_payload:
        if entry.get("name") == my_name and entry.get("slot") is not None:
            return int(entry["slot"])

        for p in entry.get("players", []):
            if p.get("name") == my_name or p.get("alias") == my_name:
                return int(p.get("slot"))

        for slot_str, info in entry.get("slot_info", {}).items():
            if info.get("name") == my_name:
                try:
                    return int(slot_str)
                except ValueError:
                    continue

    return None
