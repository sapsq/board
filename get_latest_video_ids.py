import requests
from bs4 import BeautifulSoup
import json


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


def extract_video_ids(data: dict, username:str) -> list:
    """
    Extract video IDs from the parsed JSON data.

    Args:
        data (dict): Parsed JSON data.

    Returns:
        list: List of video IDs.
    """
    video_list = data['source']['data'][f'/embed/@{username}']['videoList']
    return [video['id'] for video in video_list]


def main():

    username = "itsthathelim"
    url = f'https://www.tiktok.com/embed/@{username}'

    print(f"Searching for latest videos for: {username}")
    data = fetch_tiktok_embed(url)
    print("Data:", data)
    video_ids = extract_video_ids(data, username)
    print("Video IDs:", video_ids)
    print(json.dumps(video_ids))


if __name__ == "__main__":
    main()
