import yt_dlp as yt
from pytube import Playlist

DL_PATH = r'F:\\Eigene Medien\\SHOOTINGS\\Reel-Workfolder\\full tracks\\'


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
        'outtmpl': DL_PATH + filename,  # cant handle "/", creates folder
    }

    with yt.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])

    print("Download complete... {}".format(filename))


def txt_runner():
    print("Reading File..")
    youtube_links = readfile()
    print("Start downloading..")
    for link in youtube_links:
        run(link)
    print("Finished downloading all.")


def pl_linkrunner():
    link = input("Please enter the playlist link: ")
    yt_playlist = Playlist(link)
    for video in yt_playlist.videos:
        run(video.watch_url)
    print("Finished downloading playlist.")


pl_linkrunner()
