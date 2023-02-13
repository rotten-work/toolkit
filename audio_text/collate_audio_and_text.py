import os

output = 'lex_orig_audio_text_train_filelist.txt'

audio_dir = 'Lexington_original_22050Hz'
text_path = 'lexington_original.txt'

folder_name = 'lex_orig'

audios = os.listdir(audio_dir)

with open(text_path, encoding='utf-8') as f:
    lines = [line.strip() for line in f]

lines_new = []
for audio, line in zip(audios, lines):
    line_new = f"{folder_name}/{audio}|{line}\n"
    lines_new.append(line_new)

with open(output, 'w', encoding='utf-8') as f:
    f.writelines(lines_new)