import os
from dotenv import load_dotenv
import archipelago

# Load environment variables from .env file
load_dotenv()

# Assign .env values to variables
pishock_username = os.getenv("pishock_username")
API_KEY = os.getenv("API_KEY")
SHARE_CODE = os.getenv("SHARE_CODE")
server_port = os.getenv("server_port")
archipelago_path = os.getenv("archipelago_path")
keyword = os.getenv("keyword")

# Validate that all required variables are set
required_variables = {
    "pishock_username": pishock_username,
    "API_KEY": API_KEY,
    "SHARE_CODE": SHARE_CODE,
    "server_port": server_port,
    "archipelago_path": archipelago_path,
    "keyword": keyword,
}
name = input("Enter your name: ")
archipelago.main(name, server_port, keyword, archipelago_path)