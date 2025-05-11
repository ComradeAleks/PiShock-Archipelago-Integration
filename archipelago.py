import subprocess
import os
import threading
import sys
import Pishock_API
import settings
import re

# Global reference to the subprocess instance
archipelago_process = None
ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

# Add a global flag to signal thread termination
stop_output_thread = False

def strip_ansi_codes(text):
    return ansi_escape.sub('', text)

def read_output(process):
    """Read and print the output from the subprocess, and check for traps and trackers."""
    global stop_output_thread
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break

        print(line, end="")  # for printing archipelago messages
        handle_received_item(line)

def handle_received_item(processed_line):
    line = strip_ansi_codes(processed_line.lower())
    player_name = settings.name.lower()

    # Check to see if this line is directed at whever you want to be shocked
    if (
        f"{player_name} found their " in line or
        f"to {player_name}" in line
    ):
        print(f"Detected line for {player_name}: {line}")
        check_for_traps(processed_line)

def check_for_traps(processed_line):
    if not settings.traps:
        print("No traps defined in settings. Skipping...")
        return
    if ":" in processed_line:
        print("Trap found in line, but looks to be a message. Skipping...")
        return

    for trap_name, trackers in settings.traps.items():
        if trap_name in processed_line:
            print(f"Trap found: {trap_name}")

            def send_command(tracker_name, tracker_data):
                try:
                    Pishock_API.send_vibration(
                        tracker_name,
                        tracker_data["share_code"],
                        tracker_data["mode"],
                        tracker_data["intensity"],
                        tracker_data["duration"]
                    )
                except KeyError as e:
                    print(f"Error: Missing key {e} in tracker data for {tracker_name}. Skipping...")
                except Exception as e:
                    print(f"Unexpected error while processing tracker {tracker_name}: {e}")
            # threading so that it can send multiple shocks at once
            threads = []
            for tracker_name, tracker_data in trackers.items():
                t = threading.Thread(target=send_command, args=(tracker_name, tracker_data))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

def main(Name, server_port, keyword, archipelago_path=None):
    global archipelago_process

    # Define the path to the ArchipelagoTextClient executable
    client_path = os.path.join(archipelago_path, 'ArchipelagoTextClient.exe')  # Adjust as needed

    # Check if the executable exists
    if not os.path.exists(client_path):
        print(f"Error: The ArchipelagoTextClient executable was not found at {client_path}.")
        return

    # Define the server address and port
    server_address = 'archipelago.gg'

    # Construct the command to run the text client in non-GUI mode and connect to the server
    server_url = f"archipelago://{server_address}:{server_port}"
    command = [client_path, '--nogui', server_url]

    # Print the command for debugging
    print(f"Running command: {' '.join(command)}")

    try:
        # Start the subprocess with stdin, stdout, and stderr pipes
        archipelago_process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(f"Started ArchipelagoTextClient connecting to {server_url}")

        # Wait for "Enter slot name:" to appear in the output then send the name to log in
        while True:
            line = archipelago_process.stdout.readline()
            if "Enter slot name:" in line:
                print("Logged in successfully")
                archipelago_process.stdin.write(Name + '\n')
                archipelago_process.stdin.flush() 
                break

        # Start a thread to monitor the output from the subprocess
        output_thread = threading.Thread(target=read_output, args=(archipelago_process,))
        output_thread.daemon = True
        output_thread.start()

        # Wait for the subprocess to finish
        archipelago_process.wait()

    except FileNotFoundError:
        print(f"Error: The client executable was not found at {client_path}")
    except Exception as e:
        print(f"An error occurred: {e}")



def terminate_archipelago():
    """Terminate the Archipelago subprocess if it's running."""
    global archipelago_process, stop_output_thread
    stop_output_thread = True
    if archipelago_process and archipelago_process.poll() is None:
        archipelago_process.terminate()
        archipelago_process.wait()
        archipelago_process = None

