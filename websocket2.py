import json
import asyncio
import websockets
from dataclasses import dataclass, asdict
from typing import List, Optional
import settings

@dataclass
class PublishLogData:
    u: int
    ty: str
    w: bool
    h: bool
    o: str

@dataclass
class PublishCommandBody:
    id: int
    m: str
    i: int
    d: int
    r: bool
    l: PublishLogData

@dataclass
class PublishCommand:
    Target: str
    Body: PublishCommandBody

@dataclass
class Command:
    Operation: str
    Targets: Optional[List[str]]
    PublishCommands: List[PublishCommand]

class PiShockClient:
    def __init__(self):
        self.ws_url = (
            f"wss://broker.pishock.com/v2?"
            f"Username={settings.pishock_name}"
            f"&ApiKey={settings.api_key}"
        )
        self.ws = None
        self._lock = asyncio.Lock()
        self._recv_queue = asyncio.Queue()
        self._recv_task = None
        print("WebSocket URL:", self.ws_url)

    async def connect(self, retry_interval=5):
            while True:
                try:
                    self.ws = await websockets.connect(
                        self.ws_url,
                        compression=None,
                        ping_interval=None,
                        max_size=None,
                        max_queue=None
                    )
                    self._recv_task = asyncio.create_task(self._receive_loop())
                    break  # exit loop if connection is successful
                except Exception as e:
                    print(f"Connection failed: {e}. Retrying in {retry_interval} seconds...")
                    await asyncio.sleep(retry_interval)

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                await self.handle_message(message)
        except Exception as e:
            print(f"Receive loop error: {e}")
            await self.reconnect()

    async def reconnect(self):
        if self._recv_task:
            self._recv_task.cancel()
        await self.connect()

    async def handle_message(self, message):
        print(f"Received: {message}")

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                #print("Received message:", message)
                await self._recv_queue.put(json.loads(message))
        except websockets.exceptions.ConnectionClosed as e:
            print(f"WebSocket connection closed: {e}")
        except Exception as e:
            print(f"WebSocket receive loop error: {e}")

    async def close(self):
        if self.ws and not self.ws.closed:
            await self.ws.close()
        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass

    def _build_command_packet(self, commands, repeating: bool) -> Command:
        mode_map = {
            0: "s",
            1: "v",
            2: "b",
            3: "e"
        }

        publish_commands = []

        for name, device_id, share_code, mode, intensity, duration_ms in commands:
            if int(mode) not in mode_map:
                raise ValueError(f"Unknown mode: {mode}")

            log_data = PublishLogData(
                u=int(settings.USERID),
                ty="sc",
                w=False,
                h=False,
                o="Archipelago " + str(name)
            )

            body = PublishCommandBody(
                id=int(device_id),
                m=mode_map[int(mode)],
                i=int(intensity),
                d=int(duration_ms),
                r=repeating,
                l=log_data
            )

            publish_commands.append(PublishCommand(
                Target=f"c{settings.hub_client_id}-sops-{share_code}",
                Body=body
            ))

        return Command(
            Operation="PUBLISH",
            Targets=None,
            PublishCommands=publish_commands
        )

    async def send_activation_now(self, commands: list[list[str | int]], repeating: bool = False):
        command_packet = self._build_command_packet(commands, repeating)
        payload = json.dumps(asdict(command_packet))
        #print("Sending payload:", payload)

        async with self._lock:
            try:
                await self.ws.send(payload)
                response = await asyncio.wait_for(self._recv_queue.get(), timeout=5.0)
                return response
            except asyncio.TimeoutError:
                print("Timed out waiting for server response.")
                return {"IsError": True, "Message": "Timed out waiting for response."}
            except Exception as e:
                print("Send error:", e)
                return {"IsError": True, "Message": str(e)}

    def get_device_commands(self, device_names):
        all_devices = settings.devices
        return [
            [
                name,
                str(all_devices[name]["device_id"]),
                all_devices[name]["share_code"],
                all_devices[name]["mode"],
                all_devices[name]["intensity"],
                all_devices[name]["duration"]
            ]
            for name in device_names
        ]
    
async def send_activation(device_names: list[str], client: PiShockClient):
    try:
        commands = client.get_device_commands(device_names)
        resp = await client.send_activation_now(commands)
        #print("device response:", resp)

        # Reconnect on Redis or protocol/socket errors
        if resp.get("IsError") and (
            "Redis" in resp.get("Message", "") or "Socket terminated" in resp.get("Message", "")
        ):
            print("Connection error detected. Reconnecting WebSocket...")
            while resp.get("IsError"):
                await client.close()
                await asyncio.sleep(1)
                await client.connect()
                await asyncio.sleep(1)
                resp = await client.send_activation_now(commands)
                #print("Retry response:", resp)
            print("Connected to WebSocket.")
            print("Activation sent successfully")
        else:
            print("Activation sent successfully")

    except Exception as e:
        print("Unhandled exception in send_activation:", e)
