import os
import librosa
import soundfile as sf

subtitle_file = "ruby_bbtag_manual/ruby_bbtag_manual.srt"

with open(subtitle_file, 'rb') as f:
    data = f.read().decode("utf-8")

data = data.strip()
# 注意需要区分linux和windows环境下的换行符
if "\r\n" in data:
    subtitle_chunks = data.split("\r\n\r\n")
else:
    subtitle_chunks = data.split("\n\n")

# https://pynative.com/python-convert-seconds-to-hhmmss/
def hms_to_secs(hms_str):
    # print('Time in hh:mm:ss:', hms_str)
    # split in hh, mm, ss
    hh, mm, ss = hms_str.split(':')
    return int(hh) * 3600 + int(mm) * 60 + float(ss)

subtitles = []
for chunck in subtitle_chunks:
    if "\r\n" in chunck:
        lines = chunck.split("\r\n")
    else:
        lines = chunck.split("\n")

    index = int(lines[0])

    start_to_end_str = lines[1].replace(',', '.')
    start_to_end_list = start_to_end_str.split(" ")

    start = hms_to_secs(start_to_end_list[0])
    end = hms_to_secs(start_to_end_list[2])

    time_span = [start, end]

    subtitle = [index, time_span, lines[2]]

    subtitles.append(subtitle)

output_dir = "ruby_bbtag_manual/"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

filepath = "ruby_bbtag.wav"
prefix = 'ruby_bbtag'
y, sr = librosa.load(filepath, sr=22050, mono=True)
for subtitle in subtitles:
    index_str = f'{subtitle[0]:06}'

    # https://stackoverflow.com/questions/60105626/split-audio-on-timestamps-librosa
    start = round(subtitle[1][0] * sr)
    end = round(subtitle[1][1] * sr)

    block = y[start:end]
    output_path = os.path.join(output_dir, f'{prefix}_{index_str}.wav')
    sf.write(output_path, block, 22050, 'PCM_16')
