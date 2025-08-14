import gzip
import json
import uuid
import json
import websockets
import websocket2
import settings
import asyncio

if settings.server_address.startswith("ws://"):
    SERVER_URI = f"{settings.server_address}:{settings.server_port}"
else:
    SERVER_URI     = f"wss://{settings.server_address}:{settings.server_port}" 

SLOT_NAME      = settings.archipelago_name
ITEMS_HANDLING = 0b001
SLOT_DATA      = False
Is_player      = True

if  settings.password and settings.password != "null":
    PASSWORD = settings.password
else:
    PASSWORD = ""
    
TAGS = ["Tracker", "PiShock"]
if settings.Deathlink_mode:
    TAGS.append("DeathLink")
if settings.trapLink_mode:
    TAGS.append("TrapLink")
    
    
class ArchipelagoConnectionRefused(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors
        
    def __str__(self):
        base_msg = super().__str__()
        return f"{base_msg}: The connection was refused because of the following errors: {', '.join(self.errors)}" 


async def prompt_slot_async():
    user_input = await asyncio.to_thread(input, "Enter slot/username (Enter to cancel): ")
    return user_input.strip() or None

async def prompt_password_async():
    user_input = await asyncio.to_thread(input, "Enter password (Enter to cancel): ")
    return user_input.strip() or None


def classify_refusal(errors: list[str]):
    """
    Return 'password' or 'slot' or 'both' if the ONLY error is InvalidPassword/InvalidSlot.
    Otherwise None (treat as fatal).
    """
    s = set(errors or [])
    if s == {"InvalidPassword"}:
        return "password"
    if s == {"InvalidSlot"}:
        return "slot"
    if s == {"InvalidSlot", "InvalidPassword"}:
        return "both"
    return None

async def archipelago_client(pishock_client, connected_successfully):
    slot_name = SLOT_NAME
    password = PASSWORD
    name_map = {}
    location_map = {}
    seen_locations = set()
    items_not_for_self = any([not trap.get("for_self", True) for trap in settings.traps.values()])

    print(f"Connecting to {SERVER_URI}")
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
        connected_successfully.append(True)

        # 2) Build dynamic games list for DataPackage
        games_field = room_info.get("games") or room_info.get("Games")
        server_games = list(games_field.keys()) if isinstance(games_field, dict) else games_field or []
        
        MY_SLOT_IDS = -1
        while MY_SLOT_IDS == -1:
            # 3) Send Client Connection 
            await ws.send(json.dumps([{
                "cmd":            "Connect",
                "name":           slot_name,
                "password":       password,
                "game":           None,     # Game is fetched from slot_info after presenting as a Tracker
                "uuid":           str(uuid.uuid4()),
                "version":        {"major": 0, "minor": 6, "build": 1, "class": "Version"},
                "items_handling": ITEMS_HANDLING,
                "tags":           TAGS,
                "slot_data":      SLOT_DATA
            }]))
            print("Connecting to server...")

            # 4) Connection confirmation
            connected = json.loads(await ws.recv())
            #print("Connected:", connected)
            try:
                MY_SLOT_IDS, game = get_my_slots(connected)
            except ArchipelagoConnectionRefused as ex:
                kind = classify_refusal(ex.errors)
                if kind is None:
                    raise
                
                if kind in ("slot", "both"):
                    slot_name = await prompt_slot_async()
                    if not slot_name:
                        raise

                if kind in ("password", "both"):
                    password = await prompt_password_async()
                    if not password:
                        raise
                
        if MY_SLOT_IDS is None:
            raise Exception(f"Unknown connection error: {connected}")

        # 5) Request the DataPackage for those games or just do the whole shlabang if that dont work for some reason
        dp_version = room_info.get("datapackage_version") or room_info.get("data_package_version") or 1
        dp_req = {"cmd": "GetDataPackage", "version": dp_version}
        if server_games:
            dp_req["games"] = server_games
            print(f"Fetching DataPackage for games: {server_games}")
        else:
            print("Fetching full DataPackage (all games)")
        await ws.send(json.dumps([dp_req]))

        # 6) Process DataPackage to populate name_map and location_map
        while True:
            frame = await ws.recv()
            if isinstance(frame, (bytes, bytearray)):
                try:
                    data = gzip.decompress(frame).decode()
                    pkg = json.loads(data).get('games', {}).get(game, {})
                except Exception:
                    continue
            else:
                packet = json.loads(frame)
                pkg = None
                for cmd in packet:
                    if cmd.get('cmd') == 'DataPackage':
                        pkg = cmd['data'].get('games', {}).get(game, {})
                        break
                if pkg is None:
                    continue

            # Invert mappings from DataPackage
            item_map = pkg.get('item_name_to_id', {})
            name_map = {item_id: name for name, item_id in item_map.items()}
            loc_map = pkg.get('location_name_to_id', {})
            location_map = {loc_id: name for name, loc_id in loc_map.items()}
            print(f"Loaded {len(name_map)} items and {len(location_map)} locations for {game}")
            break

        # 7) Main event loop
        print("… now listening for RoomUpdate and ReceivedItems …")
        while True:
            frame = await ws.recv()

            # Handle binary DataPackage updates
            if isinstance(frame, (bytes, bytearray)):
                continue
            packet = json.loads(frame)
            for cmd in packet:
                c = cmd.get("cmd")
                if c == "Bounced" or c == "TrapLink" or c == "DeathLink":
                    t = cmd.get("tags", [])
                    d = cmd.get("data", {})
                    #print(cmd)
                    #print(t)
                    #print(d)
                    if "TrapLink" in t or c == "TrapLink":
                        print(f"TrapLink: {d.get('source')!r} sent a {d.get('trap_name')!r}")
                        await websocket2.send_activation(settings.trapLink_devices, pishock_client)
                    if "DeathLink" in t or c == "DeathLink":
                        print(f"DeathLink from {d.get('source')!r} because of {d.get('cause')!r}")
                        await websocket2.send_activation(settings.Deathlink_devices, pishock_client)
                

                # when you get an item
                elif c == "PrintJSON" and cmd.get("type") in ["ItemSend", "ItemCheat"]:
                    # 1) checking if the item belongs to you or another player
                    Is_player = cmd.get("receiving") in MY_SLOT_IDS
                    #print(cmd)
                    sender_id = cmd.get("item", {}).get("player")
                    # 2) gets the item_id, from the JSON text field
                    if sender_id in MY_SLOT_IDS or items_not_for_self:
                        print("checking for item")
                        await check_for_items(cmd, name_map, pishock_client, Is_player)
                    break
                    
                elif c == "ReceivedItems":
                    print("checking for item")
                    await check_for_items(cmd, name_map, pishock_client, True)

                # Auto-checking locations
                elif c == "RoomUpdate":
                    new_locs = [loc for loc in cmd.get("checked_locations", []) if loc not in seen_locations]
                    for loc in new_locs:
                        seen_locations.add(loc)
                        await ws.send(json.dumps([{"cmd": "CheckLocation", "location": loc}]))

                else:
                    #print(f"Other `{c}`: {cmd!r}")
                    pass
            
  

async def check_for_items(cmd, name_map, pishock_client, Is_player):
    if cmd.get("cmd") == "ReceivedItems":
        # Received items packet.  These are 100% for the player.  Ignore PrintJSON packets that reveal items for the player.
        items = cmd.get("items")
        for item in items:
            item_id = item.get("item")
            item_name = name_map.get(item_id, "<unknown>")
            print(f"Recieved item: {item_name} (ID {item_id})")
            await check_for_traps(item_name, pishock_client, Is_player)
            
    if cmd.get("cmd") == "PrintJSON":
        for entry in cmd.get("data", []):
            if entry.get("type") == "item_id":
                # get item and print it
                item_id   = int(entry["text"])
                item_name = name_map.get(item_id, "<unknown>")
                if Is_player:
                    print(f"Recieved item: {item_name} (ID {item_id})")
                else:
                    print(f"Sent item: {item_name} (ID {item_id})")
                # activation time
                await check_for_traps(item_name, pishock_client, Is_player)

async def check_for_traps(processed_line: str, pishock_client, Is_player):
    if not settings.traps and not settings.otherChecks.get("activated"):
        print("Cannot find traps within Yaml file")
        return

    matched = False
    if settings.traps:
        for trap in settings.traps.values():
            trap_names = {x.lower() for x in trap.get("names", set())}
            if not trap_names:
                trap_name = trap.get("name", "").lower()
                if not trap_name:
                    continue
                trap_names.add(trap_name)
            
            for_self = trap.get("for_self", True)
            device_names = trap.get("devices", [])
            if any([x in processed_line.lower() for x in trap_names]) and Is_player == for_self:
                matched = True
                await websocket2.send_activation(device_names, pishock_client)
                break
    if not matched:
        # Only run if no trap matched
        other_checks = settings.otherChecks
        if other_checks.get("activated"):
            mode = other_checks.get("send/receive", "all").lower()
            devices = other_checks.get("devices", [])
            # Is_player == True means received, False means sent
            if (
                (mode == "all") or
                (mode == "send" and not Is_player) or
                (mode == "receive" and Is_player)
            ):
                await websocket2.send_activation(devices, pishock_client)

#use the connect payload to find the player slot aka your slot, and then return it for the other thingimajig
def get_my_slots(connect_payload):
    if not isinstance(connect_payload, list):
        return None, None

    for entry in connect_payload:
        if entry.get("cmd") == "ConnectionRefused":
            raise ArchipelagoConnectionRefused("Connection Refused", entry.get("errors"))
            
        if entry.get("cmd") == "Connected":
            slot = entry.get("slot")
            my_slots = [slot]
            slots = entry.get("slot_info")
            game = slots.get(str(slot)).get("game")
            for slot_number, slot_data in slots.items():
                if slot_data.get("type") == 2 and slot in slot_data.get("group_members", []):
                    my_slots.append(int(slot_number))
                
            return my_slots, game

    return None, None
