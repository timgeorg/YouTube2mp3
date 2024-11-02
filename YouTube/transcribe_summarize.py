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


class YouTubeVideo():
    def __init__(self, url):
        self.url = url
        self.logger = Logger().create_logger(self.__class__.__name__, log_level=20) 
        self.logger.info(f"Creating YouTubeVideo object for URL: {url}")
        self.soup = self._get_metadata(url)
        self.title = self._get_title()
        self.channel = self._get_channel()
        self.description = self._get_description()
        self.transcript = self._get_transcript()

    
    def _get_metadata(self, url):
        """
        Fetches and parses the metadata from the given URL.
        This method sends a GET request to the specified URL, retrieves the HTML content,
        and parses it using BeautifulSoup to extract metadata.
        Args:
            url (str): The URL from which to fetch the metadata.
        Returns:
            BeautifulSoup: A BeautifulSoup object containing the parsed HTML content.
        Raises:
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """

        self.logger.info(f"Getting metadata from {url}")
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        html = response.content
        soup = BeautifulSoup(html, features="html.parser")
        self.logger.info(f"Successfully retrieved metadata from {url}")
        return soup
    

    def _get_title(self):
        """
        Retrieves the title of a YouTube video.
        Args:
            url (str): The URL of the YouTube video.
        Returns:
            str: The title of the YouTube video if successful.
            None: If an error occurs during the retrieval process.
        Raises:
            Exception: If an error occurs while retrieving the title.
        """

        self.logger.info(f"Getting title ...")
        title_tag = self.soup.find("meta", property="og:title")
        title = title_tag["content"] if title_tag else "Title not found"
        self.logger.info(f"Title: {title}")
        return title
    

    def _get_channel(self):
        """
        Extracts the channel name from the provided BeautifulSoup object.
        Args:
            soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of a YouTube page.
        Returns:
            str: The name of the channel if found, otherwise "Channel name not found".
        """
        self.logger.info(f"Getting channel ...")
        channel_tag = self.soup.find("link", itemprop="name")
        channel_name = channel_tag["content"] if channel_tag else "Channel name not found"
        self.logger.info(f"Channel: {channel_name}")
        return channel_name
    

    def _get_description(self):
        """
        Extracts the description from a YouTube video page.
        Args:
            url (str): The URL of the YouTube video.
        Returns:
            str: The description of the YouTube video.
        """

        description_regex = re.compile('(?<=shortDescription":").*(?=","isCrawlable)')
        description = description_regex.findall(str(self.soup))[0].replace('\\n','\n')
        return description


    def _get_transcript(self):
        """
        Retrieves the transcript of a YouTube video and converts it to a timestamped format.
        Args:
            url (str): The URL of the YouTube video.
        Returns:
            list: A list of dictionaries containing the transcript with timestamps if successful.
            None: If an error occurs during the retrieval process.
        Raises:
            Exception: If an error occurs while retrieving the transcript.
        """

        self.logger.info(f"Getting transcript ...")

        video_id = self.url.split('=')[-1]

        try:
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=("de", "en"))
            timestamped_data = self._convert_transcript_to_timedelta(data)
            self.logger.info(f"Successfully retrieved transcript")
            return timestamped_data
        
        except Exception as e:
            self.logger.error(f"An error occurred while retrieving the transcript: {e}")
            return None



class YouTubeTranscribeSummarize(YouTubeVideo):

    def __init__(self, url):
        super().__init__(url)


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
            self.logger.info(f"Outline found in description. Returning outline.")
            return result
        except Exception as e:
            self.logger.info(f"No outline found in description: {e}")
            return None


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
    obj = YouTubeTranscribeSummarize(url=url)
    desc = obj.description
    outline = obj.get_outline(desc)

    if outline is None:
        pass
        # no outline, but make a summary anyway

    if outline is None:
        pass
        # check how long the transcript is and create sections if too long

    # TODO: make a summary of a short video with no outline

    # TODO: make a summary of a long video with no outline (sections)


    if outline:
        outline = obj._convert_timestamps(outline)
        sections = obj.link_content_to_outline(content=obj.transcript, outline=outline)
        chap_summaries = []

        # for section in sections:
        #     chap_summary = obj.get_chapter_summary(str(section))
        #     print(chap_summary)
        #     chap_summaries.append(chap_summary)


    # Write the summary into a markdown file

    print(chap_summaries)
    return chap_summaries



if __name__ == '__main__':

    example_summary(url='https://www.youtube.com/watch?v=W_JfzXaYNDI')






