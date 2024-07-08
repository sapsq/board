import requests
import json
import os
import sys
from typing import List

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

def process_videos(video_ids: List[str], username: str, awanllm_api_key: str, tok_api_key: str) -> List[dict]:
    new_reviews = []
    processed_video_ids = []
    
    for video_id in video_ids:
        video_url = f'https://www.tiktok.com/@{username}/video/{video_id}'
        response = transcribe(video_url, tok_api_key)
        print(response)

        description = response['data']['desc']
        cover = response['data']['video']['cover']
        transcript = response['subtitles']

        word_and_score = find_review_score(awanllm_api_key, transcript)
        print(word_and_score)

        ai_response = word_and_score['choices'][0]['message']['content']
        print(f"AI Response: {ai_response}")

        success = False
        for attempt in range(3):  # Retry up to 3 times
             try:
                # Try to parse as-is
                json_ai_response = json.loads(ai_response)
                success = True
                break
            except json.JSONDecodeError:
                # If it fails, replace single quotes with double quotes and try again
                try:
                    response_str_corrected = ai_response.replace("'", '"')
                    json_ai_response = json.loads(response_str_corrected)
                    success = True
                    break
                except json.JSONDecodeError as e:
                    print(f"Attempt {attempt + 1}: Failed to parse AI response: {e}")
        
        if not success:
            print("Failed to parse AI response after 3 attempts, skipping this video.")
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
