import requests
import json
import os
import sys
import re
from typing import List, Tuple, Union

def transcribe(video_url: str, tok_api_key: str) -> dict:
    url = 'https://tt.tokbackup.com/fetchTikTokData'
    params = {
        'video': video_url,
        'get_transcript': 'true'
    }
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,da;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://script.tokaudit.io',
        'Referer': 'https://script.tokaudit.io/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'x-api-key': tok_api_key
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def find_review_score(awanllm_api_key: str, transcript: str) -> dict:
    url = "https://api.awanllm.com/v1/chat/completions"
    payload = json.dumps({
        "model": "Meta-Llama-3-8B-Instruct",
        "messages": [
            {"role": "user", "content": f"You are a text to JSON output system, Here is a transcript of a video that is likely a food review. first output a true or false for if it is a food review based on the transcript, whats one word that would sum up the reviewers thoughts of the food, try to use their words? and output their given score for this review OUTPUT IN JSON ONLY DO NOT MAKE ANY COMMENTS DO NOT RETURN ANY OTHER TEXT!! YOU MUST RETURN json that can be parsed with json.loads() in python eg. {{'review': true, 'word': '', 'score': 10}} here is the transcript: ```{transcript}```"},
        ],
        "repetition_penalty": 1.1,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 1024,
        "stream": False
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {awanllm_api_key}"
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

def read_json(file_path: str) -> List:
    """
    Read data from a JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        List: Data read from the file.
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json(file_path: str, data: List) -> None:
    """
    Write data to a JSON file.

    Args:
        file_path (str): Path to the JSON file.
        data (List): Data to write.
    """
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def extract_json_from_response(response_str: str) -> str:
    """
    Extract JSON object from a response string that contains extra text.

    Args:
        response_str (str): Response string containing a JSON object.

    Returns:
        str: Extracted JSON string.
    """
    # Attempt to find the first JSON object in the response
    json_patterns = [r'(\{.*\})', r'(\[.*\])']
    for pattern in json_patterns:
        match = re.search(pattern, response_str, re.DOTALL)
        if match:
            return match.group(1)
    return ""

def query_ai_model(awanllm_api_key: str, transcript: str) -> dict:
    """
    Query the AI model to get a review score.

    Args:
        awanllm_api_key (str): API key for the AI model.
        transcript (str): Transcript of the video.

    Returns:
        dict: Response from the AI model.
    """
    for attempt in range(3):  # Retry up to 3 times
        response = find_review_score(awanllm_api_key, transcript)
        ai_response = response['choices'][0]['message']['content'].strip()
        json_str = extract_json_from_response(ai_response)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"Attempt {attempt + 1}: Failed to parse extracted JSON.")
        else:
            print(f"Attempt {attempt + 1}: Failed to extract JSON from AI response.")
    return {}

def process_videos(video_ids: List[str], username: str, awanllm_api_key: str, tok_api_key: str) -> Tuple[List[dict], List[str]]:
    new_reviews = []
    processed_video_ids = []
    
    for video_id in video_ids:
        video_url = f'https://www.tiktok.com/@{username}/video/{video_id}'
        response = transcribe(video_url, tok_api_key)
        print(response)

        description = response['data']['desc']
        cover = response['data']['video']['cover']
        transcript = response['subtitles']

        json_ai_response = query_ai_model(awanllm_api_key, transcript)
        
        if not json_ai_response:
            print("Failed to get valid JSON from AI model after multiple attempts, skipping this video.")
            continue

        if json_ai_response.get('review'):
            print("Determined this is a food review video.")

            full_review_object = {
                "cover": cover,
                "word": json_ai_response['word'],
                "score": json_ai_response['score'],
                "videoUrl": video_url,
                "description": description,
            }
            print(full_review_object)
            new_reviews.append(full_review_object)

        else:
            print("AI determined this is not a food review video.")

        # Add the video ID to processed_video_ids regardless of the review outcome
        processed_video_ids.append(video_id)
    
    return new_reviews, processed_video_ids

if __name__ == '__main__':
    awanllm_api_key = os.getenv('AWANLLM_API_KEY')
    tok_api_key = os.getenv('TOK_API_KEY')
    username = "itsthathelim"
    
    if len(sys.argv) != 2:
        print("Usage: python process_videos.py <comma-separated-video-ids>")
        sys.exit(1)
    
    video_ids = sys.argv[1].split(',')
    new_reviews, processed_video_ids = process_videos(video_ids, username, awanllm_api_key, tok_api_key)
    
    # Update reviews.json
    existing_reviews = read_json('reviews.json')
    write_json('reviews.json', existing_reviews + new_reviews)
    
    # Update processed_videos.json
    existing_processed_videos = read_json('processed_videos.json')
    write_json('processed_videos.json', existing_processed_videos + processed_video_ids)
