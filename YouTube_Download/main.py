import yt_dlp as yt


def readfile():
    file = open('link.txt', 'r')
    urls = []
    for line in file:
        urls.append(line)
    return urls


def download_MP3(url):
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


def download_Video(url):
    video_url = url
    video_info = yt.YoutubeDL().extract_info(
        url=video_url, download=False
    )
    filename = f"{video_info['title']}.mp4"
    options = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'keepvideo': True,
        'outtmpl': filename,
    }

    with yt.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])

    print("Download complete... {}".format(filename))


def handle_input():
    userinput = input("Please enter the YouTube link: \n")

    if 'youtube' in userinput:
        print("Downloading single YouTube video as MP3")
        download_MP3(userinput)
        print("Finished downloading MP3.")
    else:
        print("No valid input")

if __name__ == '__main__':
    handle_input()
