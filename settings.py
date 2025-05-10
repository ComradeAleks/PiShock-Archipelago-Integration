import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Assign .env values to variables
pishock_username = os.getenv("pishock_username")
API_KEY = os.getenv("API_KEY")
SHARE_CODE = os.getenv("SHARE_CODE")
server_port = os.getenv("server_port")
archipelago_path = os.getenv("archipelago_path")
keyword = os.getenv("keyword")
name = os.getenv("name")


mode = "1"  # 0 = Shock, 1 = vibration, 2 = BEEP
intensity = "100"
duration = "1000"




# [trap name] [SHARE_CODE] [mode] [intensity] [duration] [pishock message]