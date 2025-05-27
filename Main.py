import asyncio
import arc_connect
import win32api
import win32con
import atexit
import sys
import nest_asyncio
nest_asyncio.apply()

# Store the PiShock client globally
pishock_client = None

def handle_exit(signum=None, frame=None):
    terminate_archipelago()
    print("Exiting...")
    sys.exit(0)

def terminate_archipelago():
    """Terminate the Archipelago subprocess if it's running."""
    global archipelago_process, stop_output_thread
    stop_output_thread = True
    if archipelago_process and archipelago_process.poll() is None:
        archipelago_process.terminate()
        archipelago_process.wait()
        archipelago_process = None

def on_close_event(ctrl_type):
    if ctrl_type == win32con.CTRL_CLOSE_EVENT:
        print("Window is being closed. Running cleanup...")
        handle_exit()
        with open("log.txt", "a") as f:
            f.write("Window closed by user.\n")
        return True
    return False    

win32api.SetConsoleCtrlHandler(on_close_event, True)
atexit.register(lambda: print("Program exited normally."))

# Establish connection at program start
async def run():
    global pishock_client
    from websocket2 import PiShockClient  # Import here to avoid circular imports
    pishock_client = PiShockClient()
    print("Connecting to WebSocket...")
    await pishock_client.connect()
    print("Connected to WebSocket.")
    await arc_connect.archipelago_client(pishock_client)  # pass client into your logic

try:
    while True:
        asyncio.run(run())
except KeyboardInterrupt:
    print("Caught KeyboardInterrupt. Exiting...")
    sys.exit(0)
