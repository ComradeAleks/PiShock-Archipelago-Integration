import asyncio
import settings
import arc_connect
import win32api
import win32con
import atexit
import sys



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

#  close event handler
win32api.SetConsoleCtrlHandler(on_close_event, True)
atexit.register(lambda: print("Program exited normally."))

# Loop for closing the window and running the program
try:
    while True:
        asyncio.run(arc_connect.archipelago_client())
except KeyboardInterrupt:
    print("Caught KeyboardInterrupt. Exiting...")
    sys.exit(0)