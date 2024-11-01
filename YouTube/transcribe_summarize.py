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

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utilities.logger import Logger


class YouTubeTranscribeSummarize(Logger):

    def __init__(self, logging_level='DEBUG') -> None:
        self.create_logger(logging_level)

    def get_transcript(self, url='https://www.youtube.com/watch?v=W_JfzXaYNDI'):
        """
        Retrieves the transcript of a YouTube video and converts it to a timestamped format.
        Args:
            url (str): The URL of the YouTube video. Defaults to 'https://www.youtube.com/watch?v=W_JfzXaYNDI'.
        Returns:
            list: A list of dictionaries containing the transcript with timestamps if successful.
            None: If an error occurs during the retrieval process.
        Raises:
            Exception: If an error occurs while retrieving the transcript.
        """
        self.logger.info(f"Getting transcript from {url}")

        video_id = url.split('=')[-1]

        try:
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=("de", "en"))
            timestamped_data = self._convert_transcript_to_timedelta(data)
            self.logger.info(f"Successfully retrieved transcript from {url}")
            return timestamped_data
        
        except Exception as e:
            self.logger.error(f"An error occurred while retrieving the transcript: {e}")
            return None


    def _convert_transcript_to_timedelta(self, data):
        """
        Converts transcript data to include end time, minutes, seconds, and timestamp.
        Args:
            data (list of dict): A list of dictionaries where each dictionary represents a transcript item 
                with 'start' and 'duration' keys.
        Returns:
            list of dict: The modified list of dictionaries with additional keys:
                - 'end_time': The end time of the transcript item.
                - 'minutes': The minute part of the end time.
                - 'seconds': The second part of the end time.
                - 'timestamp': A timedelta object representing the end time.
        """

        for item in data:
            item["end_time"] = item['start'] + item['duration']
            end_time = float(item['start']) + float(item['duration'])
            minutes, seconds = divmod(end_time, 60)
            item["minutes"] = minutes
            item["seconds"] = seconds
            item["timestamp"] = timedelta(minutes=item["minutes"], seconds=item["seconds"])

        return data


    def get_description(self, url):
        """
        Extracts the description from a YouTube video page.
        Args:
            url (str): The URL of the YouTube video.
        Returns:
            str: The description of the YouTube video.
        """
        self.logger.info(f"Getting description from {url}")
        soup = BeautifulSoup(requests.get(url).content, features="html.parser")
        pattern = re.compile('(?<=shortDescription":").*(?=","isCrawlable)')
        description = pattern.findall(str(soup))[0].replace('\\n','\n')
        return description


    def get_outline(self, description):
        load_dotenv()

        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 
                'content': 
                    'If the following video description contains an outline, return the outline as a JSON list with "timestamp" and "topic". \
                        The one key containing this list shall be called "timestamps".\
                        If there is no outline, return "No outline found in description.".'},

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

        try:
            result = json.loads(result)
            return result
        except Exception as e:
            print("No outline found in description: {e}")
            return None

        # TODO code below into separate function

    def _convert_timestamps(self, result):

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


    def link_content_to_outline(self, content, outline):

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


    def get_chapter_summary(self, section, model='gpt-4o-mini'):

        client = OpenAI(api_key=os.getenv('OPENAI_API'))

        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 
                'content': 
                    'Summarize the following section of the video. \
                        Use the provided content to generate a summary of the section. \
                        Stay in the original language. \
                        Create Bullet Points, but dont shorten the idea of the content. Explain the topic briefly and not that they talk about it in the video. \
                        Answer the question thats given in the topic or chapter title if available. Put the topic as a heading. '},

                {'role': 'user', 'content': section}
            ],
            temperature=0.08,
            max_tokens=512,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        result = response.choices[0].message.content
        return result
    
def example_summary(url):
    # url = 'https://www.youtube.com/watch?v=W_JfzXaYNDI'
    summary = YouTubeTranscribeSummarize()
    desc = summary.get_description(url)
    print(desc)
    outline = summary.get_outline(desc)
    outline = summary._convert_timestamps(outline)
    sections = summary.link_content_to_outline(content=summary.get_transcript(url), outline=outline)
    print(sections)
    chap_summaries = []
    for section in sections:
        chap_summary = summary.get_chapter_summary(str(section))
        print(chap_summary)
        chap_summaries.append(chap_summary)

    print(chap_summaries)
    return chap_summaries



if __name__ == '__main__':

    example_summary(url='https://www.youtube.com/watch?v=W_JfzXaYNDI')






