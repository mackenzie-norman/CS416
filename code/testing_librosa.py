from scipy import signal,io
from scipy.fft import fft, fftfreq
from scipy.io.wavfile import write, read
import numpy as np
import sounddevice as sd
import math
import librosa
BUFFER_SIZE = 2048
# Play a tone on the computer.
def play(rate, wav):
    # Deal with stereo.
    channels = 1
    if wav.ndim == 2:
        channels = 2

    # Set up and start the stream.
    stream = sd.RawOutputStream(
        samplerate = rate,
        blocksize = BUFFER_SIZE,
        channels = channels,
        dtype = 'float32',
    )

    # Write the samples.
    stream.start()
    # https://stackoverflow.com/a/73368196
    indices = np.arange(BUFFER_SIZE, wav.shape[0], BUFFER_SIZE)
    samples = np.ascontiguousarray(wav, dtype=np.float32)
    for buffer in np.array_split(samples, indices):
        stream.write(buffer)

    # Tear down the stream.
    stream.stop()
    stream.close()

wav = read("./code/sounds/gc.wav")
sample_rate = wav[0]
wav = wav[1]
# [:num_secs* sample_rate]
wav = wav.astype(np.float32)
play(sample_rate, wav)
y_tritone = librosa.effects.pitch_shift(wav, sr=sample_rate, n_steps=-6)
play(sample_rate, y_tritone)