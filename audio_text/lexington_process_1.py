import os
import glob
import librosa
import numpy as np
import soundfile as sf

input_dir = 'lexington_fanwork_bad/'
output_dir = 'lexington_fanwork_22050Hz_bad/'

# filepaths = list(
#     filter(os.path.isfile, 
#     glob.glob(os.path.join(input_dir, '*')))
# )
# filepaths.sort(key=lambda f: int("".join(filter(str.isdigit, 
#     os.path.splitext(f)[0])))
# )

filenames = os.listdir(input_dir)
filepaths = []
for filename in filenames:
    filepath = os.path.join(input_dir, filename)
    filepaths.append(filepath)

# Python program to check if a path exists
# if it doesn’t exist we create one
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

index = 116
for filepath in filepaths:
    print(filepath)
    y, sr = sf.read(filepath)
    # y, sr = librosa.load(filepath, sr=22050, mono=True)
    try:
        y = librosa.resample(y, orig_sr=sr, target_sr=22050)
    except:
        print(f"the bad file is: {filepath}")
    index_str = f'{index:06}'
    output_path = os.path.join(output_dir, f'{index_str}.wav')
    sf.write(output_path, y, 22050, 'PCM_16')
    index += 1