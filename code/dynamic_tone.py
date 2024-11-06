from scipy import signal,io
from scipy.fft import fft, fftfreq
import numpy as np
import sounddevice as sd
import math
BUFFER_SIZE = 2048
def knob(s, offset=5.0):
    if s < 0.1:
        return 0
    db = 3.0 * (s - offset)
    a = 10.0 ** (db / 20.0)
    return a
# Build filters.
def make_filter(freqs, btype):
    global sample_rate
    freqs = 2.0 * np.array(freqs, dtype=np.float64) / sample_rate
    fir_windows = 255
    return  signal.firwin(
            fir_windows,
            freqs,
            pass_zero=btype,
        )
def do_filter_window_wise(filter, sub_channel, zi):
    
    return signal.lfilter(filter, [1.], sub_channel, zi=zi)
    #ff = do_filter(filter, sub_channel)
    #sub_channels
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

def do_filter( f, channels):
    return signal.lfilter(f, [1.], channels)

def write_wav(filename, rate, data):
    assert data.dtype == np.float64
    #data *= 32767
    data = data.astype(np.int16)
    io.wavfile.write(filename, rate, data)
import sounddevice
from scipy.io.wavfile import write, read
#ft = 'ba'
# Apply filters.
#emphasis = (knob(0), knob(0), knob(20))
#maybe scale the values?
#zi  = signal.lfilter_zi(filter_treble,1)
#ret_val = do_filter_window_wise(filter_bass, wav)
#filters = (filter_bass, filter_mid, filter_treble)
#channels = np.transpose(wav)

#filtered = np.array(tuple(e * do_filter_window_wise( f, channels)
            #for e, f in zip(emphasis, filters)))
#gain = 1
#out_data = out_data.astype(np.int16)

def main():
    num_secs = 4
    wav = read("./code/sounds/gc.wav")
    global sample_rate
    sample_rate = wav[0]
    wav = wav[1]
    # [:num_secs* sample_rate]
    wav = wav.astype(np.float64)
    low_pass = 300
    high_pass = 2000
    gain = 0.5
    #make our filters
    filter_bass = make_filter(low_pass, 'lowpass')
    filter_mid = make_filter((low_pass,high_pass), 'bandpass')
    filter_treble = make_filter(high_pass, 'highpass')
    #get intial values
    bass_zi  = signal.lfilter_zi(filter_bass,1)
    mid_zi  = signal.lfilter_zi(filter_mid,1)
    treble_zi  = signal.lfilter_zi(filter_treble,1)

    #split channels into n bins 
    w_size = 1024
    n_bins = len(filter_bass)
    n_bins = int(len(wav)/w_size)
    sub_channels = np.array_split(wav,n_bins )
    #all our arrays, it might be smarter to sum them earlier and keep one final array
    bass_final = np.array([])
    mid_final = np.array([])
    treble_final = np.array([])
    for sub_channel in sub_channels:
        window = signal.windows.cosine(len(sub_channel)) 
        sub_channel = sub_channel * window
        fft_values =  np.absolute(fft(sub_channel))

        freq = [f for i, f in enumerate(fftfreq(len(sub_channel), 1/sample_rate)) if f > 0]
        fft_values = [fft_values[i]  for i,f in enumerate(freq) ]
        
        #return(0)
        low_bins = [i for i,f in enumerate(freq) if f < low_pass and f > 0]
        low_power = np.mean([fft_values[i] for i in low_bins])
        mid_bins = [i for i,f in enumerate(freq) if f > low_pass and f < high_pass]
        mid_power = np.mean([fft_values[i] for i in mid_bins])

        high_bins = [i for i,f in enumerate(freq) if f > high_pass]
        high_power = np.mean([fft_values[i] for i in high_bins])
        min_power = min(low_power, mid_power, high_power)
        low_ratio = min_power / low_power  
        mid_ratio = min_power / mid_power  
        high_ratio = min_power / high_power  
        #high_ratio = 1
        bass_level = knob(5 *low_ratio)
        fr, bass_zi = do_filter_window_wise(filter_bass, sub_channel, bass_zi)
        bass_final = np.append(bass_final, fr)
        fr *= bass_level
        mid_level = knob(5 *mid_ratio)
        fr, mid_zi = do_filter_window_wise(filter_mid, sub_channel, mid_zi)
        fr *= mid_level
        mid_final = np.append(mid_final, fr)
        treble_level = knob(5*high_ratio)
        fr, treble_zi = do_filter_window_wise(filter_treble, sub_channel, treble_zi)
        fr *= treble_level
        treble_final = np.append(treble_final, fr)
    filtered = np.array([bass_final,mid_final,treble_final])

    result = gain * np.sum(filtered, axis=0)
    play(sample_rate,result)
    write_wav("./code/sounds/test_eq.wav", sample_rate, result)
main()