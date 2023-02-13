import os
import glob
import librosa
import soundfile as sf

input_dir = 'lexington_data/'
output_dir = 'lexington_original_22050Hz/'

filepaths = list(
    filter(os.path.isfile, 
    glob.glob(os.path.join(input_dir, '*')))
)
filepaths.sort(key=lambda f: int("".join(filter(str.isdigit, 
    os.path.splitext(f)[0])))
)

# Python program to check if a path exists
# if it doesn’t exist we create one
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

index = 116
for filepath in filepaths:
    print(filepath)
    y, sr = librosa.load(filepath, sr=22050, mono=True)
    index_str = f'{index:06}'
    output_path = os.path.join(output_dir, f'{index_str}.wav')
    sf.write(output_path, y, 22050, 'PCM_16')
    index += 1