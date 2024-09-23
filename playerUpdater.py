# update_players.py
import gspread
from google.oauth2.service_account import Credentials
from cryptography.fernet import Fernet
import json


def load_encrypted_json():
    with open("secret.key", "rb") as key_file:
        key = key_file.read()

    with open("autoupdater.json.enc", "rb") as enc_file:
        encrypted_data = enc_file.read()

    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()

    return json.loads(decrypted_data)


def load_old_players():
    try:
        with open('players.txt', 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()


def update_oldplayers_file(removed_players):
    with open('oldplayer.txt', 'a') as f:
        for player in removed_players:
            f.write(player + "\n")


def playerUpdater():
    creds_data = load_encrypted_json()
    creds = Credentials.from_service_account_info(creds_data, scopes=["https://www.googleapis.com/auth/spreadsheets",
                                                                      "https://www.googleapis.com/auth/drive"])

    client = gspread.authorize(creds)
    spreadsheet_key = "1D3FjM-tUAPhpwKPt_7QVwbDAkhDp45PRIzPLFePJupE"
    sheet = client.open_by_key(spreadsheet_key).worksheet("Members of Parliament")

    data = sheet.get('B6:D35')

    new_players = set("\t".join(row) for row in data)
    old_players = load_old_players()

    # Find removed players
    removed_players = old_players - new_players

    # Update players.txt
    with open('players.txt', 'w') as f:
        f.write("\n".join(new_players))

    # Update oldplayer.txt with removed players
    if removed_players:
        update_oldplayers_file(removed_players)

    print(f"players.txt has been updated! {len(removed_players)} players removed.")


if __name__ == "__main__":
    playerUpdater()
