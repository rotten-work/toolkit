import os

input_dir = 'lexington_fanwork_22050Hz/'

filenames = os.listdir(input_dir)
filepaths = []
for filename in filenames:
    filepath = os.path.join(input_dir, filename)
    filepaths.append(filepath)

index = 116
for filepath in filepaths:
    print(filepath)
    index_str = f'{index:06}'
    dest_path = os.path.join(input_dir, f'{index_str}.wav')
    os.rename(filepath, dest_path)
    index += 1