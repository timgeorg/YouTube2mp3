from pytube import YouTube

# Function to download video
def download_video(url, path='.'):
    
  ... .filter(progressive=True, file_extension='mp4')
  ... .order_by('resolution')
  ... .desc()
  ... .first()
  ... .download()
    try:
        # Create a YouTube object
        yt = YouTube(url)
        
        # Get the highest resolution stream available
        stream = yt.streams.get_highest_resolution()
        
        # Download the video
        stream.download(output_path=path)
        
        print(f"Download completed! Video saved to {path}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == "__main__":
    video_url = input("Enter the YouTube video URL: ")
    download_path = input("Enter the download path (leave empty for current directory): ") or '.'
    print("Started download.")

    YouTube('url').streams.first().download()
    yt = YouTube('url')
    yt.streams
    filter(progressive=True, file_extension='mp4')
  ...order_by('resolution')
  ... .desc()
  ... .first()
  ... .download()


    print("FInished downloading video.")
