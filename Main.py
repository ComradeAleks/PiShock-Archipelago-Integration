
import settings
import archipelago
import win32api
import win32con
import atexit
import sys



def handle_exit(signum=None, frame=None):
    archipelago.terminate_archipelago()
    print("Exiting...")
    sys.exit(0)

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
        archipelago.main(settings.name, settings.server_port, settings.keyword, settings.archipelago_path)
except KeyboardInterrupt:
    print("Caught KeyboardInterrupt. Exiting...")
    sys.exit(0)