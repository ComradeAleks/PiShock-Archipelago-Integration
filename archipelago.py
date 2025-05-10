import subprocess
import os
import threading
import sys
import Pishock_API
import settings

# Global reference to the subprocess instance
archipelago_process = None

# Add a global flag to signal thread termination
stop_output_thread = False

def read_output(process):
    """Read and print the output from the subprocess, and check for traps and trackers."""
    global stop_output_thread
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:  # Stop reading if the process is terminated
            break

        print(line, end="")  # Print the output to the console

        # Ignore everything before the word "found" and check for traps in the rest of the line
        if "found" in line:
            processed_line = line.split("found", 1)[1]  # Keep only the part after "found"

            # Check for each trap in the processed line
            if not settings.traps:  # If no traps are defined, skip processing
                print("No traps defined in settings. Skipping...")
                continue

            for trap_name, trackers in settings.traps.items():
                if trap_name in processed_line:
                    # If the trap is found, iterate over its trackers
                    for tracker_name, tracker_data in trackers.items():
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

def monitor_user_input():
    """Monitor user input and terminate the process if 'quit' is entered."""
    global stop_output_thread
    while True:
        user_input = input()
        if user_input.strip().lower() == "quit":
            terminate_archipelago()
            print("Exiting...")
            sys.exit(0)  # Exit the script

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

        # Immediately send the Name variable to the subprocess
        # Wait for "Enter slot name:" to appear in the output
        while True:
            line = archipelago_process.stdout.readline()
            if "Enter slot name:" in line:
                print("Logged in successfully")
                archipelago_process.stdin.write(Name + '\n')  # Send the Name variable
                archipelago_process.stdin.flush()  # Ensure the input is sent immediately
                break

        # Start a thread to monitor the output from the subprocess
        output_thread = threading.Thread(target=read_output, args=(archipelago_process,))
        output_thread.daemon = True
        output_thread.start()

        # Start a thread to monitor user input
        input_thread = threading.Thread(target=monitor_user_input)
        input_thread.daemon = True
        input_thread.start()

        # Wait for the subprocess to finish
        archipelago_process.wait()

    except FileNotFoundError:
        print(f"Error: The client executable was not found at {client_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def terminate_archipelago():
    """Terminate the Archipelago subprocess if it's running."""
    global archipelago_process, stop_output_thread
    stop_output_thread = True  # Signal the output thread to stop
    if archipelago_process and archipelago_process.poll() is None:  # Check if the process is still running
        archipelago_process.terminate()  # Send termination signal
        archipelago_process.wait()  # Wait for the process to fully terminate
        archipelago_process = None


