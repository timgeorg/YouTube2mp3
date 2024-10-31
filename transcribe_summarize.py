from youtube_transcript_api import YouTubeTranscriptApi
from datetime import timedelta
import re
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv # pip install python-dotenv
import os
# from openai import AzureOpenAI
from openai import OpenAI
import json


def get_transcript(url='https://www.youtube.com/watch?v=W_JfzXaYNDI'):
    """
    Retrieves the transcript of a YouTube video and processes it to include additional time-related information.
    Args:
        url (str): The URL of the YouTube video. Defaults to 'https://www.youtube.com/watch?v=W_JfzXaYNDI'.
    Returns:
        list: A list of dictionaries, each containing the transcript data for a segment of the video. Each dictionary includes:
            - 'start': The start time of the segment in seconds.
            - 'duration': The duration of the segment in seconds.
            - 'end_time': The end time of the segment in seconds.
            - 'minutes': The end time of the segment in minutes.
            - 'seconds': The remaining seconds after converting end time to minutes.
            - 'timestamp': A timedelta object representing the end time of the segment.
    """

    video_id = url.split('=')[-1]

    data = YouTubeTranscriptApi.get_transcript(video_id, languages=("de", "en"))

    for item in data:
        item["end_time"] = item['start'] + item['duration']
        end_time = float(item['start']) + float(item['duration'])
        minutes, seconds = divmod(end_time, 60)
        item["minutes"] = minutes
        item["seconds"] = seconds
        item["timestamp"] = timedelta(minutes=item["minutes"], seconds=item["seconds"])

    return data


def get_description(url):
    """
    Extracts the description from a YouTube video page.
    Args:
        url (str): The URL of the YouTube video.
    Returns:
        str: The description of the YouTube video.
    """
    soup = BeautifulSoup(requests.get(url).content, features="html.parser")
    pattern = re.compile('(?<=shortDescription":").*(?=","isCrawlable)')
    description = pattern.findall(str(soup))[0].replace('\\n','\n')
    return description


def get_outline(description):
    load_dotenv()

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 
            'content': 
                'If the following video description contains an outline, return the outline as a JSON list with "timestamp" and "topic". Else return nothing"'},

            {'role': 'user', 'content': description}
        ],
        temperature=0.08,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={ "type": "json_object" }
    )

    result = response.choices[0].message.content
    result = result.replace("\n", "").rstrip().lstrip().replace("  ", "")
    result = json.loads(result)

    outlist = result["timestamps"]

    for item in outlist:
        time_parts = item["timestamp"].split(":")
        if len(time_parts) == 2:  # Format is "MM:SS"
            minutes, seconds = map(int, time_parts)
            item["timestamp"] = timedelta(minutes=minutes, seconds=seconds)
        elif len(time_parts) == 3:  # Format is "HH:MM:SS"
            hours, minutes, seconds = map(int, time_parts)
            item["timestamp"] = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        else:
            raise ValueError(f"Unexpected timestamp format: {item['timestamp']}")

    return outlist


def link_content_to_outline(content, outline):

    for item in outline:
        item["content"] = []
        start_time = item["timestamp"]
        end_time = outline[outline.index(item) + 1]["timestamp"] if outline.index(item) + 1 < len(outline) else None
        
        for entry in content:
            if end_time:
                if start_time <= entry["timestamp"] < end_time:
                    item["content"].append(entry["text"])
            else:
                if entry["timestamp"] >= start_time:
                    item["content"].append(entry["text"])

    for item in outline:
        item["content"] = " ".join(item["content"])

    print(outline)

    return outline


def get_chapter_summary(section, model='gpt-4o-mini'):

    client = OpenAI(api_key=os.getenv('OPENAI_API'))

    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 
            'content': 
                'Summarize the following section of the video. Use the provided content to generate a summary of the section. Stay in the original language. Create Bullet Points.'},

            {'role': 'user', 'content': section}
        ],
        temperature=0.08,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    result = response.choices[0].message.content
    return result



if __name__ == '__main__':


    url = 'https://www.youtube.com/watch?v=W_JfzXaYNDI'
    desc = get_description(url)
    print(desc)
    outline = get_outline(desc)
    sections = link_content_to_outline(get_transcript(url), outline)
    print(sections)
    chap_summaries = []
    for section in sections:
        chap_summary = get_chapter_summary(section["content"])
        print(chap_summary)
        chap_summaries.append(chap_summary)

    print(chap_summaries)






