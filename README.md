# Archipelago + PiShock Integration

This program allows you to integrate [PiShock](https://pishock.com) devices with the [Archipelago Randomizer](https://archipelago.gg), enabling in-game events like deathlink or item/trap collection to trigger your PiShock devices (such as for vibration, beeping, or general activation).

## Important Rules

* Do not use words related to self-harm to describe problems and/or discussing this program while within the archipelago discord server (“PiShock,” is ofcourse still allowed). Use alternative terms like `activation`, `device`, or similar.

---

## Setup Instructions

1. **Install the newest release.**
2. **Open the configuration file** (`config.yaml`) in any text editor (VS Code is recommended for clarity).
3. **Fill out the necessary fields** as described below.

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
  Device_name:              # Device name can be anything, just dont have spaces
    device_id: 12345        # this is the id of your PiShock device
    share_code: ShareCode   # this is the sharecode of The same PiShock device
    mode: 2                 # 0 = activation, 1 = vibrate, 2 = beep
    intensity: 100          # 0–100 (100 is max)
    duration: 1000          # In milliseconds (1000ms = 1 second)
# just copy the block under for every device you want, but dont forget the spaces.
  Device_name_2:            
    device_id: 12345        
    share_code: ShareCode   
    mode: 2                 
    intensity: 100          
    duration: 1000          
```

* **Device_name:** Can be anything (no spaces allowed), but the name must match references in `deathlink` and `traps`.
* You can add as many devices as needed by repeating the format under `devices:`.

---

### `deathlink`

Configure which devices activate when a *DeathLink* event occurs (shared player deaths).

```yaml
deathlink:
  activated: false               
  devices: [Device_name, Device_name_2]
```

* Set `activated` to `true` to enable DeathLink or `false` to dsable it.
* List all device names you want to activate (from the `devices` you created)  with a comma and space `, ` inbetween.
* **Important:** Do not use the same device multiple times.

---

### `traps`

Traps allow you to bind in-game checks (like item checks or Trap items) to your devices.

```yaml
traps:
  Check_name_1: [Device_name, Device_name_2]
  Check_name_2: [Device_name_2]
```

* The **Check_name** must exactly match the item check name as it appears in the Archipelago client or game logic.
* Device names must match entries in the `devices` section you created earlier.
* You can assign multiple devices to one trap, or reuse devices across different traps, but you CAN NOT use the same device twice or more in one trap.
* you can add as many **Check_name**s as you wish, just remember to have them under `traps` and not give two of them the same name

---

## Important Rules

* Do not use words related to self-harm to describe problems within the archipelago discord server (“PiShock,” is ofcourse still allowed).
* Use alternative terms like `activation`, `device`, or similar.

---

## Example:

```yaml
devices:
  Belt:
    device_id: 12345
    share_code: ABCDEF1234
    mode: 1
    intensity: 75
    duration: 1500
```

```yaml
traps:
  BeeTrap: [Belt]
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
