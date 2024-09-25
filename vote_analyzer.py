import praw
import re
import tkinter as tk
from tkinter import scrolledtext
from playerUpdater import playerUpdater
import configparser
import datetime
import regex as re

# Fixed player data file (adjust the file path accordingly)
playerUpdater()
PLAYER_DATA_FILE = 'players.txt'

config = configparser.ConfigParser()
config.read('config.ini')

# Initialize PRAW Reddit instance using the credentials from the file
reddit = praw.Reddit(client_id=config['reddit']['client_id'],
                     client_secret=config['reddit']['client_secret'],
                     user_agent=config['reddit']['user_agent'])


def load_old_players(filename):
    old_players = {}

    with open(filename, 'r') as f:
        for line in f:
            if not line.strip():
                continue

            parts = line.strip().split('\t')
            if len(parts) != 3:
                print(f"Skipping malformed line in {filename}: {line.strip()}")
                continue

            riding, name, party = parts
            old_players[name.lower()] = (riding.strip(), party.strip())

    return old_players

def load_player_data(filename):
    player_data = {}
    vacant_count = 0  # Initialize vacant count

    with open(filename, 'r') as file:
        for line in file:
            if line.strip() == "" or line.startswith(("Electoral District", "Party List")):
                continue
            riding, name, party = line.strip().split('\t')
            if name.lower() == 'vacant':
                vacant_count += 1
            else:
                player_data[name.lower()] = (riding.strip(), party.strip())

    return player_data, vacant_count

def should_ignore_vote(current_author, old_players, player_data):
    current_riding = player_data.get(current_author, (None,))[0]
    if current_riding:
        for old_author, (old_riding, _) in old_players.items():
            # Normalize the riding names for comparison
            if old_riding.lower() == current_riding.lower():
                return True  # Ignore if there's a matching old player's vote
    return False


def analyze_votes(submission, player_data, old_players):
    votes = {}
    all_votes = {}
    non_voters = set(player_data.keys())  # This will be updated to reflect direct replacements
    old_voters = set()
    replaced_ridings = set()  # To track ridings where old players have voted
    party_breakdown = {}

    aye_pattern = re.compile(r'\b(aye|oui|yea){e<=1}\b', re.IGNORECASE)
    nay_pattern = re.compile(r'\b(nay|non|contre){e<=1}\b', re.IGNORECASE)
    abstain_pattern = re.compile(r'\b(abstain|abstention){e<=3}\b', re.IGNORECASE)

    current_time = datetime.datetime.utcnow()
    submission.comments.replace_more(limit=None)

    for comment in submission.comments.list():
        author = comment.author.name.lower() if comment.author else None
        submission_age_days = (current_time - datetime.datetime.utcfromtimestamp(submission.created_utc)).days

        if submission_age_days > 3 or (author and (author in player_data or author in old_players)):
            comment_text = comment.body
            all_votes[author] = (comment_text, player_data.get(author, ('Unknown', 'Indy')))

            if author in old_players:
                old_voters.add(author)
                riding, party = old_players[author]

                # If the old player voted, mark their riding as "replaced"
                replaced_ridings.add(riding)

                # Process the vote for the old player
                if aye_pattern.search(comment_text.lower()):
                    votes[author] = ('aye', riding, party, comment.created_utc)
                    party_breakdown[party] = party_breakdown.get(party, 0) + 1
                elif nay_pattern.search(comment_text.lower()):
                    votes[author] = ('nay', riding, party, comment.created_utc)
                    party_breakdown[party] = party_breakdown.get(party, 0) + 1
                elif abstain_pattern.search(comment_text.lower()):
                    votes[author] = ('abstain', riding, party, comment.created_utc)

                # Remove any new players in the same riding from non_voters
                for player, (player_riding, _) in player_data.items():
                    if player_riding == riding:
                        non_voters.discard(player)  # Remove the new player if they exist
                continue

            if author in player_data:
                riding, party = player_data[author]

                # If the riding has already been replaced by an old player, skip this new player
                if riding in replaced_ridings:
                    continue

                comment_text_lower = comment_text.lower()
                if aye_pattern.search(comment_text_lower):
                    votes[author] = ('aye', riding, party, comment.created_utc)
                    party_breakdown[party] = party_breakdown.get(party, 0) + 1
                elif nay_pattern.search(comment_text_lower):
                    votes[author] = ('nay', riding, party, comment.created_utc)
                    party_breakdown[party] = party_breakdown.get(party, 0) + 1
                elif abstain_pattern.search(comment_text_lower):
                    votes[author] = ('abstain', riding, party, comment.created_utc)

    all_mps = set(player_data.keys()) - non_voters  # Ensure new players from replaced ridings are removed
    voted_mps = set(votes.keys())

    # Non-voters should exclude any players in replaced ridings
    non_voters = all_mps - voted_mps

    # Keep party information for no longer MPs who voted
    no_longer_mps = {author: (all_votes[author][0], old_players.get(author, ('Unknown', 'Indy'))[1])
                     for author in all_votes if author not in player_data}

    # Final vote tally
    final_votes = {}
    for author, (vote_type, riding, party, timestamp) in votes.items():
        if author not in final_votes or final_votes[author][3] < timestamp:
            final_votes[author] = (vote_type, riding, party, timestamp)

    return final_votes, all_votes, non_voters, no_longer_mps, old_voters



def display_vote_breakdown(final_votes, all_votes, player_data, vacant_count, old_players):
    # Clear the text box
    breakdown_box.config(state=tk.NORMAL)  # Enable editing to insert text
    breakdown_box.delete(1.0, tk.END)

    # Tally the votes
    tally = {'Aye': 0, 'Nay': 0, 'Abstain': 0}
    party_tally = {}
    no_longer_mps = {}  # For those who voted but are no longer in player_data

    # Detailed Breakdown with Line Highlighting for those who voted
    for author, (comment_text, (riding, party)) in all_votes.items():
        vote_type = final_votes.get(author, [None])[0]
        line_text = f"({riding})\t{author.capitalize()} [{party}]: {comment_text}\n"

        if author in player_data:
            # Highlight vote types
            if vote_type == 'aye':
                breakdown_box.insert(tk.END, line_text, 'green_bg')
            elif vote_type == 'nay':
                breakdown_box.insert(tk.END, line_text, 'red_bg')
            elif vote_type == 'abstain':
                breakdown_box.insert(tk.END, line_text, 'yellow_bg')
            else:
                breakdown_box.insert(tk.END, f"{line_text.strip()} - No Vote\n", 'no_vote_bg')
        else:
            # Track those no longer in player_data (i.e., no longer MPs)
            old_riding, old_party = old_players.get(author, ('Unknown', 'Indy'))
            no_longer_mps[author] = (
            all_votes[author][0], old_party, old_riding)  # Store comment text, party, and riding

    # Tally votes from final_votes
    tally_box.delete(1.0, tk.END)
    tally_text = "\nTally of Votes:\n"

    for voter, (vote_type, riding, party, _) in final_votes.items():
        tally[vote_type.capitalize()] += 1

        # Party breakdown
        if party not in party_tally:
            party_tally[party] = {'Aye': 0, 'Nay': 0, 'Abstain': 0, 'No Vote': 0}
        party_tally[party][vote_type.capitalize()] += 1

    # Number of people who haven't voted
    voted_people = set(final_votes.keys())
    all_people = set(player_data.keys())
    not_voted = all_people - voted_people

    # Display people who haven't voted
    if not_voted:
        breakdown_box.insert(tk.END, "\n--- People Who Haven't Voted ---\n", 'no_vote_bg')
        for name in not_voted:
            if name in player_data:
                riding, party = player_data[name]
                breakdown_box.insert(tk.END, f"({riding})\t{name.capitalize()} [{party}]: No Vote\n", 'no_vote_bg')

            # Track "No Vote" for each party
            if party not in party_tally:
                party_tally[party] = {'Aye': 0, 'Nay': 0, 'Abstain': 0, 'No Vote': 1}
            else:
                party_tally[party]['No Vote'] += 1

    # Final Tally Output
    tally_text += f"Aye: {tally['Aye']}\n"
    tally_text += f"Nay: {tally['Nay']}\n"
    tally_text += f"Abstain: {tally['Abstain']}\n"
    tally_text += f"Vacant seats: {vacant_count}\n"  # Add Vacant count to the tally

    # Party breakdown
    tally_text += "\nParty Breakdown:\n"
    for party, counts in party_tally.items():
        tally_text += f"{party}: Aye: {counts['Aye']}, Nay: {counts['Nay']}, Abstain: {counts['Abstain']}, No Vote: {counts['No Vote']}\n"

    tally_text += f"\nNumber of people who haven't voted: {len(not_voted)}\n"

    # Display people who voted but are no longer MPs
    if no_longer_mps:
        breakdown_box.insert(tk.END, "\n--- Voted but No Longer MPs ---\n", 'no_vote_bg')
        for author, (comment_text, party, riding) in no_longer_mps.items():
            breakdown_box.insert(tk.END, f"{author.capitalize()} [{party}] ({riding}): {comment_text.strip()}\n",
                                 'no_vote_bg')

    tally_box.insert(tk.END, tally_text)

    # Make the breakdown read-only after updating it
    breakdown_box.config(state=tk.DISABLED)

# Function to handle the analyze button click
def analyze_votes_gui():
    reddit_link = entry_link.get()  # Get the Reddit link from the input box

    # Load player data from the fixed player file
    player_data, vacant_count = load_player_data(PLAYER_DATA_FILE)

    # Load old players from oldplayer.txt
    old_players = load_old_players('oldplayer.txt')

    # Get the Reddit submission from the link
    submission = reddit.submission(url=reddit_link)

    # Analyze votes
    final_votes, all_votes, non_voters, no_longer_mps, old_voters = analyze_votes(submission, player_data, old_players)

    # Display the results and tally, passing old_players as well
    display_vote_breakdown(final_votes, all_votes, player_data, vacant_count, old_players)


# Set up the GUI
window = tk.Tk()
window.title("Vote Analyzer")

# Input box for Reddit link
label_link = tk.Label(window, text="Enter Reddit Link:")
label_link.pack()
entry_link = tk.Entry(window, width=50)
entry_link.pack()

# Button to trigger analysis
analyze_button = tk.Button(window, text="Analyze Votes", command=analyze_votes_gui)
analyze_button.pack()

# Text area for displaying the breakdown
breakdown_box = scrolledtext.ScrolledText(window, width=80, height=20)
breakdown_box.pack()

# Text area for displaying the tally
tally_box = scrolledtext.ScrolledText(window, width=60, height=20)
tally_box.pack()

# Define tag styles for highlighting
breakdown_box.tag_config('green_bg', background='lightgreen')
breakdown_box.tag_config('red_bg', background='lightcoral')
breakdown_box.tag_config('yellow_bg', background='lightyellow')
breakdown_box.tag_config('no_vote_bg', background='lightgray')

window.mainloop()
