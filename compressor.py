from pydub import AudioSegment

def compress_mp3(input_file, output_file, bitrate='16k'):
    audio = AudioSegment.from_mp3(input_file)
    audio.export(output_file, format='mp3', bitrate=bitrate)

# Usage example
input_file = 'Rieck.mp3'
output_file = 'output.mp3'
compress_mp3(input_file, output_file)

