import settings
import Pishock_API
import threading

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