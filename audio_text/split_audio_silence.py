import os

# https://stackoverflow.com/questions/45526996/split-audio-files-using-silence-detection
# Import the AudioSegment class for processing audio and the 
# split_on_silence function for separating out silent chunks.
from pydub import AudioSegment
from pydub.silence import split_on_silence

# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)

# Load your audio.
audio_path = "ruby_bbtag.wav"
audio = AudioSegment.from_file(audio_path)
audio = audio.set_frame_rate(22050)
audio = audio.set_channels(1)

# Split track where the silence is 2 seconds or more and get chunks using 
# the imported function.
chunks = split_on_silence(
    # Use the loaded audio.
    audio, 
    # Specify that a silent chunk must be at least 0.22 seconds or 200 ms long.
    min_silence_len = 200,
    # Consider a chunk silent if it's quieter than -16 dBFS.
    # (You may want to adjust this parameter.)
    silence_thresh = -50
)

# Process each chunk with your parameters
for i, chunk in enumerate(chunks):
    index = i + 1

    # Create a silence chunk that's 0.25 seconds (or 250 ms) long for padding.
    silence_chunk = AudioSegment.silent(duration=250, frame_rate=22050)

    # Add the padding chunk to beginning and end of the entire chunk.
    audio_chunk = silence_chunk + chunk + silence_chunk

    # Normalize the entire chunk.
    # normalized_chunk = match_target_amplitude(audio_chunk, -20.0)

    # Export the audio chunk.
    export_dir = "ruby_bbtag_silence"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    prefix = "bbtag_silence"
    print("Exporting chunk{0}.wav.".format(index))
    audio_chunk.export(
        f"{export_dir}/{prefix}_{index:06}.wav",
        format = "wav"
    )