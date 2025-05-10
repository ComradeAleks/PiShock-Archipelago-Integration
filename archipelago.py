import subprocess
import os
import threading
import sys

# Global reference to the subprocess instance
archipelago_process = None

# Add a global flag to signal thread termination
stop_output_thread = False

def read_output(process, keyword):
    """Read and print the output from the subprocess, and check for a specific word."""
    global stop_output_thread
    start_logging = False
    target_message = (
        "Now that you are connected, you can use !help to list commands to run via the server. "
        "If your client supports it, you may have additional local commands you can list with /help."
    )

    for line in process.stdout:
        if stop_output_thread or process.poll() is not None:  # Stop reading if the process is terminated
            break

        if not start_logging:
            if target_message in line:
                start_logging = True
            continue

        print(line, end="")  # Print the output to the console

        if keyword in line:
            print("The word was found")

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
    client_path = os.path.join(archipelago_path, 'ArchipelagoTextClient')  # Adjust as needed

    # Define the server address and port
    server_address = 'archipelago.gg'

    # Construct the command to run the text client in non-GUI mode and connect to the server
    server_url = f"archipelago://{server_address}:{server_port}"
    command = [client_path, '--nogui', server_url]

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

        # Wait for "Enter slot name:" before sending the Name variable
        while True:
            line = archipelago_process.stdout.readline()
            if not line:
                break
            print(line, end="")
            if "Enter slot name:" in line:
                archipelago_process.stdin.write(Name + '\n')  # Send the Name variable
                archipelago_process.stdin.flush()  # Ensure the input is sent immediately
                break

        # Start a thread to monitor the output from the subprocess
        output_thread = threading.Thread(target=read_output, args=(archipelago_process, keyword))
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


