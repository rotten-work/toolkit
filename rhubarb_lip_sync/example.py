import json
import wave
import time

import pyaudio

with open("output.json", encoding = 'utf-8') as f:
    data = json.load(f)

duration = data['metadata']['duration']
print(duration)

mouth_cues = data['mouthCues']

wf = wave.open("test.wav", 'rb')

p = pyaudio.PyAudio()

rate = wf.getframerate()
print(rate)

mouth_cues_index = 0
frame = 0
def callback(in_data, frame_count, time_info, status):
    global frame
    global mouth_cues_index
    # http://files.portaudio.com/docs/v19-doxydocs/structPaStreamCallbackTimeInfo.html
    # print(f"inputBufferAdc_time: {time_info['input_buffer_adc_time']}")
    # print(f"currentTime: {time_info['current_time']}")
    # print(f"outputBufferDacTime: {time_info['output_buffer_dac_time']}")
    # t = time_info['output_buffer_dac_time']

    t = frame / rate
    print(f"current time: {t}")
    while mouth_cues_index < len(mouth_cues):
        if t < mouth_cues[mouth_cues_index]['start']:
            break
        
        # 如果逻辑走到这里，说明要刷新口型了
        index = mouth_cues_index
        print(mouth_cues[index]['start'])

        next_index = index
        while t >= mouth_cues[next_index]['start']:
            next_index += 1
            if next_index >= len(mouth_cues):
                break
        
        index = next_index - 1
        print(f"current index: {index}")
        # 这里得到mouth_shape，用于口型表现
        mouth_shape = mouth_cues[index]['value']
        print(f"mouth shape: {mouth_shape}")
        mouth_cues_index = next_index

    frame += frame_count

    data = wf.readframes(frame_count)
    return (data, pyaudio.paContinue)

stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                stream_callback=callback)

stream.start_stream()

while stream.is_active():
    print("waiting...")
    time.sleep(0.2)

stream.stop_stream()
stream.close()
wf.close()

p.terminate()