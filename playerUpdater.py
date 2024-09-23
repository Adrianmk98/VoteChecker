# update_players.py
import gspread
from google.oauth2.service_account import Credentials
from cryptography.fernet import Fernet
import json



def load_encrypted_json():
    # Load the encryption key
    with open("secret.key", "rb") as key_file:
        key = key_file.read()

    # Load the encrypted data
    with open("autoupdater.json.enc", "rb") as enc_file:
        encrypted_data = enc_file.read()

    # Decrypt the data
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()

    # Return the loaded JSON data
    return json.loads(decrypted_data)


def playerUpdater():
    # Load the decrypted credentials
    creds_data = load_encrypted_json()

    # Use the loaded credentials to authorize
    creds = Credentials.from_service_account_info(creds_data, scopes=["https://www.googleapis.com/auth/spreadsheets",
                                                                      "https://www.googleapis.com/auth/drive"])

    client = gspread.authorize(creds)

    # Use the spreadsheet key directly
    spreadsheet_key = "1D3FjM-tUAPhpwKPt_7QVwbDAkhDp45PRIzPLFePJupE"  # Use the actual spreadsheet key here
    sheet = client.open_by_key(spreadsheet_key).worksheet("Members of Parliament")

    data = sheet.get('B6:D35')

    data_as_text = "\n".join(["\t".join(row) for row in data])

    with open('players.txt', 'w') as f:
        f.write(data_as_text)

    print("players.txt has been updated!")



# Call the playerUpdater function if this script is run directly
if __name__ == "__main__":
    playerUpdater()
