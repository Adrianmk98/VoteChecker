import praw
import re
import tkinter as tk
from tkinter import scrolledtext

# Fixed player data file (adjust the file path accordingly)
PLAYER_DATA_FILE = 'players.txt'

# Initialize Reddit API client
reddit = praw.Reddit(
        client_id='X',
        client_secret='X',
        user_agent='X'
    )


def load_player_data(filename):
    player_data = {}
    vacant_count = 0  # Define inside the function

    with open(filename, 'r') as file:
        for line in file:
            if line.strip() == "" or line.startswith(("Electoral District", "Party List")):
                continue
            riding, name, party = line.strip().split('\t')
            if name.lower() == 'vacant':
                vacant_count += 1  # Increment vacant count
            else:
                player_data[name.lower()] = (riding, party)

    return player_data, vacant_count  # Return both player data and vacant count


# Analyze votes in a Reddit post
def analyze_votes(submission, player_data):
    votes = {}
    all_votes = {}

    # Regex patterns for aye, nay, abstain (in English and French)
    aye_pattern = re.compile(r'\b(aye|oui|yea)\b', re.IGNORECASE)
    nay_pattern = re.compile(r'\b(nay|non|contre)\b', re.IGNORECASE)
    abstain_pattern = re.compile(r'\b(abstain|Abstention)\b', re.IGNORECASE)  # Add French word for abstain if known

    # Fetch all comments in the post
    submission.comments.replace_more(limit=None)
    for comment in submission.comments.list():
        author = comment.author.name.lower() if comment.author else None

        if not author or author not in player_data:
            continue  # Skip if author not in player data or deleted

        # Check for 'aye', 'nay', or 'abstain' in comment, case-insensitive
        comment_text = comment.body.lower()
        if aye_pattern.search(comment_text):
            votes[author] = ('aye', player_data[author][0], player_data[author][1], comment.created_utc)
        elif nay_pattern.search(comment_text):
            votes[author] = ('nay', player_data[author][0], player_data[author][1], comment.created_utc)
        elif abstain_pattern.search(comment_text):
            votes[author] = ('abstain', player_data[author][0], player_data[author][1], comment.created_utc)

        # Store all votes for detailed breakdown
        all_votes[author] = (comment_text, player_data[author])

    # Filter votes to keep only the newest one for each player
    final_votes = {}
    for author, (vote_type, riding, party, timestamp) in votes.items():
        if author not in final_votes or final_votes[author][3] < timestamp:
            final_votes[author] = (vote_type, riding, party, timestamp)

    return final_votes, all_votes


def display_vote_breakdown(final_votes, all_votes, player_data, vacant_count):
    # Clear the text box
    breakdown_box.config(state=tk.NORMAL)  # Enable editing to insert text
    breakdown_box.delete(1.0, tk.END)

    # Tally the votes
    tally = {'Aye': 0, 'Nay': 0, 'Abstain': 0}
    party_tally = {}

    # Detailed Breakdown with Line Highlighting for those who voted
    for author, (comment_text, (riding, party)) in all_votes.items():
        vote_type = final_votes.get(author, [None])[0]
        line_text = f"({riding})\t{author.capitalize()} [{party}]: {comment_text}\n"

        if vote_type == 'aye':
            breakdown_box.insert(tk.END, line_text, 'green_bg')
        elif vote_type == 'nay':
            breakdown_box.insert(tk.END, line_text, 'red_bg')
        elif vote_type == 'abstain':
            breakdown_box.insert(tk.END, line_text, 'yellow_bg')
        else:
            breakdown_box.insert(tk.END, f"{line_text.strip()} - No Vote\n", 'no_vote_bg')

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

    tally_box.insert(tk.END, tally_text)

    # Make the breakdown read-only after updating it
    breakdown_box.config(state=tk.DISABLED)




# Function to handle the analyze button click
def analyze_votes_gui():
    reddit_link = entry_link.get()  # Get the Reddit link from the input box

    # Load player data from the fixed player file
    player_data, vacant_count = load_player_data(PLAYER_DATA_FILE)

    # Get the Reddit submission from the link
    submission = reddit.submission(url=reddit_link)

    # Analyze votes
    final_votes, all_votes = analyze_votes(submission, player_data)

    # Display the results and tally
    display_vote_breakdown(final_votes, all_votes, player_data, vacant_count)



# Create the GUI window
root = tk.Tk()
root.title("Reddit Vote Analyzer")

# Link entry
tk.Label(root, text="Enter Reddit Post Link:").pack(pady=5)
entry_link = tk.Entry(root, width=50)
entry_link.pack(pady=5)

# Analyze button
analyze_button = tk.Button(root, text="Analyze Votes", command=analyze_votes_gui)
analyze_button.pack(pady=10)

# Breakdown text box (scrollable)
tk.Label(root, text="Breakdown of All Votes:").pack(pady=5)
breakdown_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=15)
breakdown_box.pack(pady=5)

# Tally text box (scrollable)
tk.Label(root, text="Tally of Votes:").pack(pady=5)
tally_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15)
tally_box.pack(pady=5)

# Text tag configuration for line highlighting
breakdown_box.tag_configure('green_bg', background='lightgreen', foreground='black')
breakdown_box.tag_configure('red_bg', background='lightcoral', foreground='black')
breakdown_box.tag_configure('yellow_bg', background='lightyellow', foreground='black')
breakdown_box.tag_configure('no_vote_bg', background='lightgray', foreground='black')  # New tag for no votes


# Start the GUI event loop
root.mainloop()
