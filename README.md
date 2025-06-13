# Archipelago + PiShock Integration

This program allows you to integrate [PiShock](https://pishock.com) devices with the [Archipelago Randomizer](https://archipelago.gg), enabling in-game events like deathlink or item/trap collection to trigger your PiShock devices (such as for vibration, beeping, or general activation).

## Important Rules

* Do not use words related to self-harm to describe problems and/or discussing this program while within the archipelago discord server (“PiShock,” is ofcourse still allowed). Use alternative terms like `activation`, `device`, or similar.

---

## Setup Instructions

1. **Install the newest release.**
2. **Open the configuration file** (`config.yaml`) in any text editor (VS Code is recommended for clarity).
3. **Fill out the necessary fields** as described below.

**Important** All ShareCodes must be Claimed for this to work, claim them by going to your PiShock Controll panel, then Click the three lines in bottom left corner and click Shared Code, place your sharecode within there and it should be good.

---

## YAML Configuration Guide

### `archipelago`

Configure your connection to the Archipelago multiworld server.

```yaml
archipelago:
  room_code: 1235           # Your Archipelago room code
  name: YourName            # Your player name in the Archipelago session
  game: YourGame            # The game you're playing in Archipelago
  password: null            # Password for the room (use null if no password)
```

---

### `PiShock`

These are your credentials for PiShock.

```yaml
pishock:
  username: YourPiShockName # Your PiShock account username
  api_key: YourAPIKEY       # Your unique API key (you get it from the website under "Account")
  client_id: 12345          # Your Hub client ID
```

You can find these on your [PiShock dashboard](https://pishock.com/#/login).

---

### `devices`

Define each PiShock-compatible device you want to use.

```yaml
devices:
  Device-1:              
    name: Device_name       # Device name can be anything you want
    device_id: 12345        # this is the id of your PiShock device
    share_code: ShareCode   # this is the sharecode of The same PiShock device
    mode: 2                 # 0 = activation, 1 = vibrate, 2 = beep
    intensity: 100          # 0–100 (100 is max)
    duration: 1000          # In milliseconds (1000ms = 1 second)
# just copy the block under for every device you want, but dont forget the spaces.
  Device-2:
    name: Device_name        
    device_id: 12345        
    share_code: ShareCode   
    mode: 2                 
    intensity: 100          
    duration: 1000          
```

* **name:** Can be anything, but the name must match references in `deathlink`, `traps` and `otherChecks`.
* You can add as many devices as needed by repeating the format under `devices:`.
* **Important** when adding more devices, make sure `Device-(number)` dont have the same number with other devices as shown above with `Device-1` and `Device-2`

---

### `deathlink/trapLink`

Configure which devices activate when a *DeathLink* or/and *TrapLink* event occurs (shared player deaths/shared player traps).

```yaml
deathlink:
  activated: false               
  devices: [Device_name, Device_name_2]
```
```yaml
trapLink:
  activated: false               
  devices: [Device_name, Device_name_2]
```

* Set `activated` to `true` to enable DeathLink/trapLink or `false` to dsable it.
* List all device names you want to activate (from the `devices` you created)  with a comma and space `, ` inbetween.
* **Important:** Do not use the same device multiple times on the same link.

---

### `traps`

Traps allow you to bind in-game checks (like item checks or Trap items) to your devices.

```yaml
traps:
  trap-1:
    name: Item_check-1                    # name of the item check
    for_self: true                        # true/false if its for you
    devices: [Device_name, Device_name_2] # devices to trigger
  trap-2:
    name: Item_check-2
    for_self: false
    devices: [Device_name, Device_name_2]
```

* The **name** must exactly match the item check name as it appears in the Archipelago client or game logic.
* **for_self** should be `true` if its an item that is for yourself, and `false` if the item check is for someone else
* Device names must match entries in the `devices` section you created earlier.
* You can assign multiple devices to one trap, or reuse devices across different traps, but you CAN NOT use the same device twice or more in one trap.
* you can add as many item checks as you want, but remember to have them under `traps:` and remember that `trap-(number)` needs to have a unique number

---

### `Other checks`

**OtherChecks** lets you set up devices to activate on ALL other item checks that has something to do with you, that isnt already triggered by an existing item check from the traps section. 

```yaml
OtherChecks:
  activated: false                        # true/false if activated or not
  send/receive: all                       # send, receive, all
  devices: [Device_name, Device_name_2]   # devices to trigger
```
* **activated** should be `true` if you want other items to activate the PiShock devices or `false`, if you dont want that.
* **send/receive** should be `send` if you want only items you send to others to trigger the devices, `receive` if you want only items you receive to trigger the devices, or `all` if you want all items that has something to do with you to trigger the devices.
* **devices** works like previously where you can not use the same device multiple times, and you need to have the device name be exactly the same as the one you created in that section.

---

## Example:

```yaml
devices:
  trap-1:
    name: Belt
    device_id: 12345
    share_code: ABCDEF1234
    mode: 1
    intensity: 75
    duration: 1500
```

```yaml
traps:
  trap-1:
    name: Bee trap
    for_self: true
    devices: [Belt]
```

---

## Support

If you run into any issues:

* **Open an Issue** on GitHub.
* **Ask on Discord:** You can find me in the Archipelago Randomizer or PiShock Discord servers. Feel free to ping me directly on the mod page or in support channels, do NOT send me friend requests or try to dm me.

* **Archipelago server:** PiShock intigration.
* **PiShock server:** Archipelago intigration. 

---

## Disclaimer

This program is intended for **fun, and for enhancing gameplay**

* **Do not** use this program in any way that could lead to harm or injury.
* If you experience pain or discomfort, **stop use immediately**.
* Do **not** use this program if you have any medical conditions, implanted devices, as per PiShock regulations.
* **I do not**  support any sort of self harm and/or suicidal thoughts, and if you do or think of doing that, you should seek out help immediately.

Always use PiShock responsibly. You are responsible for your own safety.

ENJOY!
