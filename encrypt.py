from cryptography.fernet import Fernet
import json
import os

# Generate a key and save it (only do this once)
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
    return key

# Load or generate a key
if not os.path.exists("secret.key"):
    key = generate_key()
else:
    with open("secret.key", "rb") as key_file:
        key = key_file.read()

# Load your existing data from autoupdater.json
with open("autoupdater.json", "r") as json_file:
    data = json.load(json_file)

# Convert data to JSON and encrypt it
fernet = Fernet(key)
encrypted_data = fernet.encrypt(json.dumps(data).encode())

# Save the encrypted data to a file
with open("autoupdater.json.enc", "wb") as enc_file:
    enc_file.write(encrypted_data)

print("Encryption complete. Encrypted data saved to autoupdater.json.enc.")
