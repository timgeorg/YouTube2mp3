import yt_dlp as yt

DL_PATH = r'F:\\Eigene Medien\\SHOOTINGS\\Reel-Workfolder\\full tracks\\'


def readfile():
    file = open('link.txt', 'r')
    urls = []
    for line in file:
        url = line
        urls.append(url)
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
        'outtmpl': DL_PATH + filename,
    }

    with yt.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])

    print("Download complete... {}".format(filename))


if __name__ == '__main__':
    print("Reading File..")
    youtube_links = readfile()
    print("Start downloading..")
    for link in youtube_links:
        run(link)
    print("Finished downloading all.")
