import json
import base64

with open("hurina-467613-e2c16a824e24.json") as f:
    creds = json.load(f)

creds["private_key"] = base64.b64encode(creds["private_key"].encode()).decode()

with open("credentials_base64.json", "w") as f:
    json.dump(creds, f)
