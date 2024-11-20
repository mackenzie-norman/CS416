import mido, sounddevice
import numpy as np
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from queue import Queue, Empty
def pick_midi(default = None):
    input_ports = mido.get_input_names()
    if default is None:
        prompt_str = "\n".join([f"{i + 1}. {port}" for i,port in enumerate(input_ports) ])
        sel = int(input(f"Input ports:\n{prompt_str}\nPlease enter a number between 1 and {len(input_ports) }:")) - 1
    else:
        sel = default -1
    assert sel <= len(input_ports) +1
    return input_ports[sel]
# this is needed for plotting

def update_plot(frame):
    """This is called by matplotlib for each plot update.

    Typically, audio callbacks happen more frequently than plot updates,
    therefore the queue tends to contain multiple blocks of audio data.

    """
    global plotdata
    block = True  # The first read from the queue is blocking ...
    while True:
        try:
            data = queue.get(block=block, timeout= 1)
        except Empty:
            break
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = data
        block = False  # ... all further reads are non-blocking
    for column, line in enumerate(lines):
        line.set_ydata(plotdata[:, column])
    return lines
# MIDI controller is currently hardwired.
controller = mido.open_input(pick_midi(default=1))

# Sample rate in sps. This doesn't need to be fixed: it
# could be set to the preferred rate of the audio output.
sample_rate = 48000
# Blocksize in samples to process. My desktop machine keeps
# up at this rate, which provides pretty good latency. Slower
# machines may need larger numbers.
blocksize = 16

queue = Queue()
downsample = 10
length = 1000 * downsample
plotdata = np.zeros((int(length), 1))
fig, ax = plt.subplots()
lines = ax.plot(plotdata)

ax.axis((0, len(plotdata), -1, 1))
ax.set_yticks([0])
ax.yaxis.grid(True)
ax.tick_params(bottom='off', top='off', labelbottom='off',
                right='off', left='off', labelleft='off')
fig.tight_layout(pad=0)
out_keys = dict()

# Set true to get a printed log message every time a key is
# pressed or released. Usually more annoying that useful.
log_notes = False

# Attack time in seconds.
attack_time = 0.020
# Release time in seconds.
release_time = 0.1

# This count of the number of samples output so far is
# used to make sure that waveforms are generated with
# the right phase.
#
# It would be great if Python provided nonlocal variables
# with static initialization. It does not.
sample_clock = 0

# Return a sine wave at frequency f over the given sample
# times t.
def sine_samples(t, f):
    return np.sin(2 * np.pi * f * t)

# Return a rising sawtooth wave at frequency f over the
# given sample times t.
def saw_samples(t, f):
    return (f * t) % 2.0 - 1.0

# Return a square wave at frequency f over the
# given sample times t.
def square_samples(t, f):
    return np.sign((f * t) % 2.0 - 1.0)

# Generate an array of frame_count sample times
# starting at sample_clock.
def sample_times(frame_count):
    return np.linspace(
        sample_clock / sample_rate,
        (sample_clock + frame_count) / sample_rate,
        frame_count,
        dtype=np.float32,
    )

wavetable = np.array(sine_samples(sample_times(640), 750.0))
nwavetable = len(wavetable)
wavetable_freq = 750.0

def wave_samples(t, f):
    step = f / wavetable_freq
    t0 = (step * t * sample_rate) % nwavetable
    int_part = np.floor(t0)
    frac_part = t0 - int_part
    i0 = int_part.astype(int)
    i1 = (i0 + 1) % nwavetable
    x0 = wavetable[i0]
    x1 = wavetable[i1]
    return x0 * frac_part + x1 * (1.0 - frac_part)

test_wavetable = False
if test_wavetable:
    test_wave = np.zeros(1, dtype=np.float32)
    for _ in range(int(sample_rate / blocksize)):
        t = sample_times(blocksize)
        test_wave = np.append(test_wave, wave_samples(t, 750))
        sample_clock += blocksize
    wav.write("test.wav", sample_rate, test_wave)
    exit(0)

# Oscillators.
oscillators = [
    sine_samples,
    saw_samples,
    square_samples,
    wave_samples,
]

# Index of current oscillator.
out_osc = 0

# Representation of a note currently being played.
class Note:
    def __init__(self, key, osc):
        self.frequency = key_to_freq(key)
        self.attack_time_remaining = attack_time
        self.out_osc = osc
        self.playing = True
        self.release_time_remaining = None

    # Note has been released.
    def release(self):
        self.release_time_remaining = release_time

    # Accept a time linspace to generate samples in.  Return
    # that many samples of note being played, or None if
    # note is over.
    def samples(self, t):
        if not self.playing:
            return None

        frame_count = len(t)
        out_frequency = self.frequency

        # Pick and generate a waveform.
        samples = oscillators[self.out_osc](t, out_frequency)

        if self.release_time_remaining is not None:
            # Do release part of ADSR envelope.
            release_time_remaining = self.release_time_remaining
            if release_time_remaining <= 0:
                self.playing = False
                return None
            # Figure out the gain at the starting time according
            # to a linear ramp.
            start_gain = release_time_remaining / release_time
            # Figure out the time after the last sample, and
            # adjust the release_time_remaining to reflect it.
            end_time = frame_count / sample_rate
            release_time_remaining -= end_time
            # Figure out the gain at the ending time according
            # to a linear ramp.
            end_gain = release_time_remaining / release_time
            # Calculate the linear slope over the samples. Make
            # sure it doesn't go below 0.0 due to finishing the
            # release in the middle.
            #
            # XXX This should probably be linear in dBFS rather than
            # linear in amplitude, but meh.
            envelope = np.clip(
                np.linspace(start_gain, end_gain, frame_count),
                0.0,
                1.0,
            )
            # Apply the per-sample gains for the release.
            samples *= envelope
            # Update the release time remaining for next pass.
            self.release_time_remaining = max(0, release_time_remaining)
        elif self.attack_time_remaining > 0.0:
            # Do attack part of ADSR envelope.
            attack_time_remaining = self.attack_time_remaining
            # Figure out the gain at the starting time according
            # to a linear ramp.
            start_gain = 1.0 - attack_time_remaining / attack_time
            # Figure out the time after the last sample, and
            # adjust the attack_time_remaining to reflect it.
            end_time = frame_count / sample_rate
            attack_time_remaining -= end_time
            # Figure out the gain at the ending time according
            # to a linear ramp.
            end_gain = 1.0 - attack_time_remaining / attack_time
            # Calculate the linear slope over the samples. Make
            # sure it doesn't go above 1.0 due to finishing the
            # attack in the middle.
            #
            # XXX This should probably be linear in dBFS rather than
            # linear in amplitude, but meh.
            envelope = np.clip(
                np.linspace(start_gain, end_gain, frame_count),
                0.0,
                1.0,
            )
            # Apply the per-sample gains for the attack.
            samples *= envelope
            # Update the attack time remaining for next pass.
            self.attack_time_remaining = attack_time_remaining

        return samples

# This callback is called by `sounddevice` to get some
# samples to output. It's the heart of sound generation in
# the synth.

def output_callback(out_data, frame_count, time_info, status):
    # Make sure to update the *global* sample clock.
    global sample_clock
    

    # A non-None status indicates that something has
    # happened with sound output that shouldn't have.  This
    # is almost always an underrun due to generating samples
    # too slowly.
    if status:
        print("output callback:", status)

    # Start with silence and maybe work up.
    samples = np.zeros(frame_count, dtype=np.float32)
    
    # If keys are pressed, generate sounds.
    if out_keys:
        # Time point in seconds for each sample.
        t = sample_times(frame_count)

        # Set of keys that need playing.
        on_keys = list(out_keys.keys())
        # Set of keys that need deleting.
        del_keys = set()
        # Generate the samples for each key and add them
        # into the mix.
        for key in on_keys:
            note = out_keys[key]
            note_samples = note.samples(t)
            if note_samples is None:
                del_keys.add(key)
                continue
            samples += note_samples

        # Close the deleted keys.
        for key in del_keys:
            del out_keys[key]

    # Adjust the gain so that each key gets louder up to
    # some maximum.  If necessary, scale to avoid clipping.
    nkeys = len(out_keys)
    if nkeys <= 8:
        samples *= 1.0 / 8.0
    else:
        samples *= 1.0 / len(out_keys)

    # Reshape to have an array of 1 sample for each frame.
    # Must write into the existing array rather than
    # accidentally copying over the parameter.
    out_data[:] = np.reshape(samples, (frame_count, 1))

    queue.put(out_data[::downsample])
    # Bump the sample clock for next cycle.
    sample_clock += frame_count
    
    #print(sample_clock)
# Calculate frequency for a 12-tone equal-tempered Western
# scale given MIDI note number. Change 440 to 432 for better
# sound </s>.
def key_to_freq(key):
    return 440 * 2 ** ((key - 69) / 12)

# Block waiting for the instrument (keyboard) to send a MIDI
# message, then handle it. Return False if the MIDI message
# wants the synthesizer to stop, True otherwise.

# Block waiting for the controller (keyboard) to send a MIDI
# message, then handle it. Return False if the MIDI message
# wants the instrument (synthesizer) to stop, True otherwise.
def process_midi_event():
    # These globals define the interface to sound generation.
    global out_keys, out_osc

    # Block until a MIDI message is received.
    mesg = controller.receive(block=False)
    if(mesg is None):
        return True

    # Select what to do based on message type.
    mesg_type = mesg.type
    # Special case: note on with velocity 0 indicates
    # note off (for older MIDI instruments).
    if mesg_type == 'note_on' and mesg.velocity == 0:
        mesg_type = 'note_off'
    # Add a note to the sound. If it is already on just
    # start it again.
    if mesg_type == 'note_on':
        key = mesg.note
        velocity = mesg.velocity / 127
        if log_notes:
            print('note on', key, mesg.velocity, round(velocity, 2))
            print(out_keys)
        out_keys[key] = Note(key, out_osc)
        
    # Remove a note from the sound. If it is already off,
    # this message will be ignored.
    elif mesg_type == 'note_off':
        key = mesg.note
        velocity = round(mesg.velocity / 127, 2)
        if log_notes:
            print('note off', key, mesg.velocity, velocity)
        if key in out_keys:
            out_keys[key].release()
    # Handle various controls.
    elif mesg.type == 'control_change':
        # XXX Hard-wired for "stop" key on Oxygen8.
        if mesg.control == 23 or mesg.control == 121:
            print('stop')
            return False
        # Change output waveform.
        #
        # XXX Hard-wired for "fast-forward" and "reverse"
        # keys on Oxygen8. Hard-coded for exactly two possible
        # waveforms.
        elif mesg.control == 21 or mesg.control == 22:
            print('program change')
            out_osc = (out_osc + 1) % 4
        # Unknown control changes are logged and ignored.
        else:
            print(f"control", mesg.control, mesg.value)
    # XXX Pitchwheel is currently logged and ignored.
    elif mesg.type == 'pitchwheel':
        pitch = round(mesg.pitch / 127, 2)
        print('pitchwheel', mesg.pitch, pitch)
    else:
        print('unknown MIDI message', mesg)
    return True

# Start audio playing. Must keep up with output from here on.
output_stream = sounddevice.OutputStream(
    samplerate=sample_rate,
    channels=1,
    blocksize=blocksize,
    callback=output_callback,
)

ani = animation.FuncAnimation(fig, update_plot, interval=30, cache_frame_data=False, blit = True)

output_stream.start()
plt.show(block = False)
plt.pause(1)
# Run the instrument until the controller stop key is pressed.
is_processing = True
while is_processing:
    is_processing = process_midi_event()
    #fig.canvas.flush_events() 
    #plt.pause(0.3)
    #animate(16)
    pass
