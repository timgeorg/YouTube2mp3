import streamlit as st
import re

from transcribe_summarize import example_summary

def summarize_youtube_video(url):
    # Placeholder function for summarizing the video
    # Replace this with actual summarization logic
    return "This is a summary of the video."

st.title("YouTube Video Summarizer")

# Input for YouTube URL
youtube_url = st.text_input("Enter YouTube URL:")

# Button to generate summary
if st.button("Generate Summary"):
    if youtube_url:
        # Regular expression to check if the URL is a valid YouTube link
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$'
        )

        if not youtube_regex.match(youtube_url):
            st.write("Please enter a valid YouTube URL.")
        else:
            summary = example_summary()
            st.write("Summary:")
            st.write("Description available:")
            st.write(summary)
    else:
        st.write("Please enter a valid YouTube URL.")