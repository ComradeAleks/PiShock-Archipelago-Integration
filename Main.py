
import settings
import archipelago
import Pishock_API

print(settings.server_port)
archipelago.main(settings.name, settings.server_port, settings.keyword, settings.archipelago_path)