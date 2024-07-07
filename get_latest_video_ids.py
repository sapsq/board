import requests
from bs4 import BeautifulSoup
import json
import os

def fetch_tiktok_embed(url: str) -> dict:
    """
    Fetch the TikTok embed page and extract JSON data from the script tag.

    Args:
        url (str): URL of the TikTok embed page.

    Returns:
        dict: Parsed JSON data from the page.
    """
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find('script', {'id': '__FRONTITY_CONNECT_STATE__', 'type': 'application/json'})

    if not script_tag:
        raise ValueError('JSON script tag not found in the HTML content.')

    return json.loads(script_tag.string)

def extract_video_ids(data: dict, username: str) -> list:
    """
    Extract video IDs from the parsed JSON data.

    Args:
        data (dict): Parsed JSON data.
        username (str): Username to find video IDs for.

    Returns:
        list: List of video IDs.
    """
    video_list = data['source']['data'][f'/embed/@{username}']['videoList']
    return [video['id'] for video in video_list]

def read_processed_videos(file_path: str) -> list:
    """
    Read the processed video IDs from the JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        list: List of processed video IDs.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def main():
    username = "itsthathelim"
    url = f'https://www.tiktok.com/embed/@{username}'
    processed_videos_file = 'processed_videos.json'

    data = fetch_tiktok_embed(url)
    video_ids = extract_video_ids(data, username)
    processed_videos = read_processed_videos(processed_videos_file)

    unprocessed_videos = [video_id for video_id in video_ids if video_id not in processed_videos]

    # Output the unprocessed video IDs as a single line string
    print(",".join(unprocessed_videos))

if __name__ == "__main__":
    main()
