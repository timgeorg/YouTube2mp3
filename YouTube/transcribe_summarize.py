# Native Libraries
import os
import re
import sys
import json
import requests
from datetime import datetime, timedelta
# External Libraries
from bs4 import BeautifulSoup
from dotenv import load_dotenv # pip install python-dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI # OR: from openai import AzureOpenAI

# User-defined Libraries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utilities.logger import Logger


class YouTubeVideo():
    def __init__(self, url):
        self.url = url
        self.logger = Logger().create_logger(name=self.__class__.__name__) 
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
            if not result["timestamps"]:
                self.logger.info(f"No outline found in description.")
                return None
            elif type(result["timestamps"]) == str:
                self.logger.info(f"No Outline found in description. Creating synthetic outline.")
                return None
            
            elif type(result["timestamps"]) == list:
                self.logger.info(f"Outline found in description. Returning outline.")
                return result
            else:
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

    def link_transcript_without_outline(self, content):

        # get max length of content
        content_length = content[-1]["timestamp"] # get timedelta object of last entry

        total_duration = content_length.total_seconds() / 60  # Convert total duration to minutes

        # Determine chunk length based on total duration
        if total_duration <= 15:
            chunk_length = timedelta(minutes=3)
        elif 15 < total_duration <= 45:
            chunk_length = timedelta(minutes=5)
        elif 45 < total_duration <= 90:
            chunk_length = timedelta(minutes=10)
        else:
            chunk_length = timedelta(minutes=15)
            
        sections = []
        section = {"timestamp": content[0]["timestamp"], "content": []}

        for entry in content:
            if entry["timestamp"] < section["timestamp"] + chunk_length:
                section["content"].append(entry["text"])
            else:
                section["content"] = " ".join(section["content"])
                sections.append(section)
                section = {"timestamp": entry["timestamp"], "content": [entry["text"]]}

        section["content"] = " ".join(section["content"])
        sections.append(section)

        for section in sections:
            section["topic"] = f"Chapter {sections.index(section) + 1}"
            section["start_time"] = str(section["timestamp"])
            section_length_words = len(section["content"].split())
            print("Section length: ", section_length_words)

        return sections


    def get_chapter_summary(self, section, model='gpt-4o-mini'):

        client = OpenAI(api_key=os.getenv('OPENAI_API'))

        self.logger.info(f"Getting summary for section: {section["topic"]}")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 
                'content': 
                    'Summarize the following section of the video. \
                        Use the provided content to generate a summary of the section. \
                        Stay in the original language. \
                        Create Bullet Points, but dont shorten the idea of the content. Explain the topic briefly and not that they talk about it in the video. \
                        If they talk about the 5 things or the 9 types or something like that, list them. \
                        Answer the question thats given in the topic or chapter title if available. \
                        Put the topic with timestamp (in h, min, sec) in the format "hh:mm:ss" as a heading.\
                        Every Heading should be a markdown ## heading. If there is no heading (eg. Chapter 1), create one out of the content provided. \
                        Try to keep it as short as possible, but as long as necessary. '},

                {'role': 'user', 'content': str(section)}
            ],
            temperature=0.08,
            max_tokens=512,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        result = response.choices[0].message.content
        return result
    

    def get_minimal_chapter_summary(self, section, model='gpt-4o-mini'):

        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 
                'content': 
                    'Summarize the following chapter of a podcast as short as possible in max. 1-2 bullet points.\
                        Stay in the original language. Keep the heading.'},

                {'role': 'user', 'content': str(section)}
            ],
            temperature=0.08,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        result = response.choices[0].message.content
        return result


    def get_unified_summary(self, sections):
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(

            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 
                'content': 
                    'Summarize the following outline of a podcast. \
                        Do not only list the topics they talk about, but briefly explain every idea you mention in the summary. \
                        Still try to keep it as short as possible. Use bullet points if possible.'},

                {'role': 'user', 'content': str(sections)}
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

    sections = []

    if outline is None:
        transcript = obj.transcript
        transcript_length = len(transcript)
        print(f"Transcript length: {transcript_length}")
        # outline = obj._convert_timestamps(transcript) # only if outline is found in description
        print(outline)
        sections = obj.link_transcript_without_outline(transcript)
        outline = "Synthetic"


    if outline is None:
        pass
        # check how long the transcript is and create sections if too long

    # TODO: make a summary of a short video with no outline

    # TODO: make a summary of a long video with no outline (sections)


    if outline:
        if outline != "Synthetic":
            outline = obj._convert_timestamps(outline)
            sections = obj.link_content_to_outline(content=obj.transcript, outline=outline)
        chap_summaries = []

        for section in sections:
            chap_summary = obj.get_chapter_summary(section)
            chap_summaries.append(chap_summary)

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    long_summary_filename = f"{obj.channel}_Summary_{current_time}.md"
    short_summary_filename = f"{obj.channel}_Short_Summary_{current_time}.md"
    unified_summary_filename = f"{obj.channel}_Unified_Summary_{current_time}.md"

    short_chapters = []
    for chapter in chap_summaries:
        short_chapter = obj.get_minimal_chapter_summary(chapter)
        short_chapters.append(short_chapter)

    # Concatenate all short chapters into one string
    concatenated_short_chapters = "\n\n".join(short_chapters)
    with open(short_summary_filename, "w", encoding='utf-8') as file:
        file.write(concatenated_short_chapters)

    # Get a unified summary of all chapters
    unified_summary = obj.get_unified_summary(concatenated_short_chapters)
    with open(unified_summary_filename, "w", encoding='utf-8') as file:
        file.write(unified_summary)

    # Write the summary into a markdown file
    print("Writing summary to file ...")
    with open(long_summary_filename, "w", encoding='utf-8') as file:
        for summary in chap_summaries:
            file.write(summary + "\n\n")
    print(f"Summary successfully written to {long_summary_filename}")

    return chap_summaries


if __name__ == '__main__':

    url = input("\n\nPlease enter the YouTube video URL: ")
    example_summary(url=url)






