import yt_dlp as yt
from pytube import Playlist


def readfile():
    file = open('link.txt', 'r')
    urls = []
    for line in file:
        urls.append(line)
    return urls


def run(url):
    video_url = url
    video_info = yt.YoutubeDL().extract_info(
        url=video_url, download=False
    )
    filename = f"{video_info['title']}.mp3"
    options = {
        'format': 'bestaudio/best',
        'keepvideo': False,
        'outtmpl': filename,  # cant handle "/", creates folder
    }

    with yt.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])

    print("Download complete... {}".format(filename))


def handle_input():
    userinput = input("Please enter: \n"
                      "- the YouTube link\n"
                      "- the YouTube playlist-link\n"
                      "- the link to a txt-file containing the links\n")

    if 'youtube' in userinput:

        if 'playlist' in userinput:
            print("Downloading playlist")
            yt_playlist = Playlist(userinput)
            for video in yt_playlist.videos:
                run(video.watch_url)
            print("Finished downloading playlist.")
        else:
            print("Downloading single YouTube-video")
            run(userinput)
            print("Finished downloading playlist.")

    elif '.txt' in userinput:
        print("Reading File..")
        youtube_links = readfile()
        print("Start downloading..")
        for link in youtube_links:
            run(link)
        print("Finished downloading all.")
    else:
        print("No valid input")


handle_input()
