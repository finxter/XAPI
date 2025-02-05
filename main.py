import requests
import csv
import os
from datetime import datetime
import secrets
import matplotlib.pyplot as plt

# Set a matplotlib style for prettier plots (without using seaborn)
plt.style.use('ggplot')

# Define the CSV output file path
csv_file_path = 'output/followers_counts.csv'

# Mapping of usernames to their X (Twitter) IDs.
# Obtain these IDs (e.g., via https://tweethunter.io/twitter-id-converter)
user_dict = {
    'elonmusk': '44196397',
    'Tesla': '13298072',
    'Cobratate': '333357345',
    'nvidia': '61559439',
    # Add more IDs here as needed.
}

# ---------------------------
# CSV Helper Functions
# ---------------------------
def read_existing_data(csv_file):
    """Read existing follower count data from a CSV file."""
    if os.path.isfile(csv_file):
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    return []


def write_data_to_csv(csv_file, data):
    """Write updated follower count data back to CSV, creating the file and folder if needed."""
    output_dir = os.path.dirname(csv_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Sort data for readability before writing
    data.sort(key=lambda x: (x['username'], x['date']))
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['date', 'username', 'followers_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


# ---------------------------
# API Fetching Function
# ---------------------------
def fetch_follower_counts(user_ids):
    """
    Fetch follower counts for a list of user IDs.
    Uses a free RapidAPI endpoint as an alternative to the paid X API.
    Get API Key here: https://rapidapi.com/Glavier/api/twitter135/playground/apiendpoint_4639f8b5-fb81-4802-89ad-c1ba79862f69
    """
    ids = ','.join(user_ids)
    url = "https://twitter135.p.rapidapi.com/v2/UsersByRestIds/"
    querystring = {"ids": ids}
    headers = {
        "x-rapidapi-key": "123abc",  # Your RapidAPI key (Replace)
        "x-rapidapi-host": "twitter135.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raises HTTPError if the response has an error status
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


# ---------------------------
# Plotting Function (Without pandas or seaborn)
# ---------------------------
def plot_follower_counts_no_pandas(csv_file):
    """
    Read the CSV file and plot follower counts over time without using pandas or seaborn.
    The function groups the data by username and plots each series as a line.
    """
    if not os.path.isfile(csv_file):
        print("CSV file not found. Cannot plot data.")
        return

    # Read the CSV using csv.DictReader
    data = []
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Convert date string to datetime object and followers_count to integer
                date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
                count = int(row['followers_count'])
                username = row['username']
                data.append({'date': date_obj, 'username': username, 'followers_count': count})
            except Exception as e:
                print("Error processing row:", row, e)

    # Group data by username
    grouped_data = {}
    for entry in data:
        uname = entry['username']
        grouped_data.setdefault(uname, []).append((entry['date'], entry['followers_count']))

    # Sort each username's data by date
    for uname in grouped_data:
        grouped_data[uname].sort(key=lambda x: x[0])

    # Create the plot
    plt.figure(figsize=(12, 8))
    for uname, values in grouped_data.items():
        dates = [item[0] for item in values]
        counts = [item[1] for item in values]
        plt.plot(dates, counts, marker='o', label=uname)

    plt.title("Follower Counts Over Time", fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Followers Count", fontsize=14)
    plt.legend(title="Username")
    plt.xticks(rotation=45)
    plt.tight_layout()  # Adjust layout to prevent clipping of tick labels
    plt.show()


# ---------------------------
# Main Process: Fetch & Record Data
# ---------------------------
def main():
    # Read previously stored data from CSV
    existing_data = read_existing_data(csv_file_path)
    existing_data_dict = {(row['date'], row['username']): row for row in existing_data}

    # Call the free API endpoint to get follower counts
    api_data = fetch_follower_counts(list(user_dict.values()))
    if api_data is None:
        print("Failed to fetch data from API.")
        return

    # Extract follower counts from the returned data
    followers_counts = {}
    for user in api_data.get('data', {}).get('users', []):
        try:
            result = user['result']
            legacy = result['legacy']
            rest_id = result['rest_id']
            followers_count = legacy['followers_count']

            # Find the username corresponding to this ID
            username = next((uname for uname, uid in user_dict.items() if uid == rest_id), None)
            if username:
                followers_counts[username] = followers_count
            else:
                print(f"Username not found for ID {rest_id}")
        except KeyError as e:
            print("Error processing data:", e)
            print(user)

    # Record today's date for the tracking log
    today = datetime.now().strftime('%Y-%m-%d')
    for username, followers_count in followers_counts.items():
        key = (today, username)
        existing_data_dict[key] = {
            'date': today,
            'username': username,
            'followers_count': str(followers_count)
        }

    # Write the updated data back to the CSV file
    data_to_write = list(existing_data_dict.values())
    write_data_to_csv(csv_file_path, data_to_write)
    print(f"Follower counts updated successfully for {today}.")

    # Plot the follower counts over time (without using pandas or seaborn)
    plot_follower_counts_no_pandas(csv_file_path)


if __name__ == '__main__':
    main()
