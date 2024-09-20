import praw
import re


# Fixed player data file (adjust the file path accordingly)
PLAYER_DATA_FILE = 'players.txt'

# Initialize Reddit API client
reddit = praw.Reddit(
        client_id='X',
        client_secret='X',
        user_agent='X'
    )

# Load player-riding data from file
def load_player_data(filename):
    player_data = {}
    with open(filename, 'r') as file:
        for line in file:
            riding, name = line.strip().split('\t')  # Assuming tab-separated values
            player_data[name.lower()] = riding
    return player_data

# Analyze votes in a Reddit post
def analyze_votes(submission, player_data):
    votes = {'aye': [], 'nay': [], 'abstain': []}

    # Regex patterns for aye, nay, abstain (in English and French)
    aye_pattern = re.compile(r'\b(aye|oui|yea)\b', re.IGNORECASE)
    nay_pattern = re.compile(r'\b(nay|non)\b', re.IGNORECASE)
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
            votes['aye'].append((author, player_data[author]))
        elif nay_pattern.search(comment_text):
            votes['nay'].append((author, player_data[author]))
        elif abstain_pattern.search(comment_text):
            votes['abstain'].append((author, player_data[author]))

    return votes

# Display vote breakdown
def display_vote_breakdown(votes):
    # Tally the votes
    tally = {
        'Aye': len(votes['aye']),
        'Nay': len(votes['nay']),
        'Abstain': len(votes['abstain'])
    }

    # Print detailed breakdown
    print("\nDetailed Breakdown:")
    for vote_type, voters in votes.items():
        if voters:
            print(f"\n{vote_type.capitalize()} Votes:")
            for voter, riding in voters:
                print(f"  - {voter.capitalize()} ({riding})")
        else:
            print(f"\nNo {vote_type} votes.")

    # Print tally of votes
    print("\nTally of Votes:")
    print(f"Aye: {tally['Aye']}")
    print(f"Nay: {tally['Nay']}")
    print(f"Abstain: {tally['Abstain']}")

# Main function
def main():
    # Ask the user for the Reddit link
    reddit_link = input("Please enter the Reddit post link: ")

    # Load player data from the fixed player file
    player_data = load_player_data(PLAYER_DATA_FILE)

    # Get the Reddit submission from the link
    submission = reddit.submission(url=reddit_link)

    # Analyze votes
    votes = analyze_votes(submission, player_data)

    # Display the results
    display_vote_breakdown(votes)

if __name__ == "__main__":
    main()
