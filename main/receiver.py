import sounddevice as sd
import time as tm
import threading
import math
from reedsolo import RSCodec


class myThread(threading.Thread):
    def __init__(self, d_sample=44100, b_len=44100):
        threading.Thread.__init__(self)
        self.d_sample = d_sample
        self.b_len = b_len

    def run(self):
        listen(self.d_sample, self.b_len)


def audio_callback(indata, frames, time, status):
    '''Saves the recorded audio date into the Buffer, which is to be analysed later by the main thread.'''

    global Buffer, exitFlag
    if exitFlag:
        thread_listening.join()
    Buffer = Buffer + indata.tolist()


def listen(def_samplerate, buf_length):
    '''Listening thread
    Starts to listen to the audio stream and calls the audio_callback function'''

    global exitFlag, Buffer
    exitFlag = False
    Buffer = []
    stream = sd.InputStream(callback=audio_callback, samplerate=def_samplerate, blocksize=buf_length, channels=1)
    with stream:
        sd.sleep(600000)


def find_frequency(indata, carrier_frequency, d_sample):
    '''Returns the amplitude of a given frequency in the given data.

    # indata: List of numbers
    # carrier_frequency: frequency to be looked for
    # Sigma: of all the sines and cosines'''

    Sigma = 0
    freq = len(indata) / d_sample * carrier_frequency
    for sample in range(len(indata)):
        Sigma += indata[sample][0] * math.e ** (-2 * freq * math.pi * sample / len(indata) * 1j)

    return abs(Sigma)


def get_encoding(data, error_correction_symbols, enc='IBM852'):
    '''Uses Reed-Solomon error-correction code to transform a String into ones and zeros which are to be send.
    # data: String of IBM852 characters
    # error_correction_symbols: Number of bytes protected against flipping
    # data_as_bits: String of ones and zeros'''

    rsc = RSCodec(2 * error_correction_symbols)

    if type(data) == type(2):
        st = (16 - len(str(bin(data))[2:])) * "0" + str(bin(data))[2:]
        a = rsc.encode(bytearray([int(st[:8], 2), int(st[8:], 2)]))
        # not wasting space for binary numbers
    else:
        a = rsc.encode(bytes(data, enc, 'replace'))
        # unknown characters are replaced with a '?'

    data_as_bits = ''.join(format(byte, '08b') for byte in a)
    return data_as_bits


def get_decoding(data, error_correction_bytes, enc='IBM852'):
    '''Decodes the String of ones and zeros produced by the get_encoding() back into the initial message.'''

    rsc = RSCodec(2 * error_correction_bytes)
    message = rsc.decode(bytearray([(int(data[i:i + 8], 2)) for i in range(0, len(data), 8)]))[0].decode(encoding=enc)
    # Cuts data into segments of 8 bits and translates them back into characters

    return message


def shift_correction(sequence, carrier_frequency, d_sample):
    '''Finds where does the impulse peak within the given sequence of data. The corresponding shift is returned.
    Later on, this information is used to examine the sequences that precisely overlay the impulses, thus making the
    difference of amplitudes between a one and a zero as big as possible.'''
    maxi = 0
    shft = 0
    sequence_size = len(sequence)
    sequence = 2*sequence
    for k in range(sequence_size):
        amp = find_frequency(sequence[k:int(sequence_size/2 + k)], carrier_frequency, d_sample)
        if amp > maxi:
            maxi = amp
            shft = k
    return shft


def skip(num):
    '''Used to skip first chunk of recorded data as it is usually corrupted.'''

    if not num:
        return 1
    else:
        return 0


def signal_processing(carrier_frequency, cushion=30, sensitivity=0.45, impulse_length=49, d_sample=44100, buffer_length=44100, enc='IMB852'):
    '''THE MAIN THREAD, where the signal gets processed.

    # carrier_frequency, integer between 1 and d_sample/2, frequency on which the data is transmitted.
    # cushion: integer, the number of bytes protected against flipping within each (255 - 2*cushion) bytes.
    # sensitivity: float between 1 and 0, if too small, some ones might be seen as zeros and vice versa, if too big
                   some zeros might be seen as ones. Right balance has to be struck.
    # impulse_length: integer, the length of one impulse.
    # d_sample: integer, default sample rate at which the audio is sampled.
    # buffer_length: integer, length of the audio buffer. Has to be divisible by chunk_size!

    # iteration: integer, shows what stage of the protocol the program is currently in.
    # silent_average: float, average amplitude of the target frequency in ambient noise.
    # average_buffer: list, used to calculate 3 chunk rolling average of the frequency amplitude.
    # true_bite_average: float, average amplitude with the chunk aligned to the center of the impulse. (after shift)
    # old_buffer: list, contains rest of the previous Buffer that haven't bin used due to the shift.
    # wanted_bits: string, contains ones and zeros extracted from the signal. By the end nothing but the message bits.
    # initial_sequence: boolean, True if the initial sequence of bits has been captured.
    # message: string, decoded data which is ready to be displayed'''

    global Buffer, exitFlag, bit

    iteration = 0
    silent_average = 0
    average_buffer = [0, 0, 0]
    true_bite_average = 0
    old_buffer = []
    wanted_bits = ""
    initial_sequence = False
    message = ""

    while True:
        # Checks whether the Buffer has data in it, if so it starts analysing it.
        if len(Buffer) == 0:
            tm.sleep(0.02)
        else:
            for i in range(skip(iteration)*int(18001/impulse_length), int(d_sample/impulse_length)):
                # Goes through the Buffer (First iteration skips some 18 thousand samples - they are usually corrupted)

                if iteration < 10:
                    # Finds average amplitude of the target frequency in ambient noise.
                    silent_average += find_frequency(Buffer[i * impulse_length:impulse_length * (1 + i)], carrier_frequency, d_sample) / 10
                    iteration += 1

                elif iteration == 10:
                    # Computes rolling average of the amplitude of the last 3 sequences to see if it is high enough.
                    # shiftpoint: used to skip n samples so that the shift correction is measured on a loud signal
                    average_buffer[i % 3] = find_frequency(Buffer[i * impulse_length:impulse_length * (1 + i)], carrier_frequency, d_sample) / 3
                    if sum(average_buffer) > 10 * silent_average:
                        iteration += 1
                        shiftpoint = int(294 / impulse_length)
                        print("\nloud frequency intercepted!!!")

                elif iteration < 11 + shiftpoint:
                    # Skips appropriate number of samples.
                    iteration += 1

                elif iteration == 11 + shiftpoint:
                    # Shifts by certain number of samples to measure the frequency in the middle of the impulses.
                    shift = shift_correction(Buffer[i * impulse_length:impulse_length * (1 + i)], carrier_frequency, d_sample)
                    iteration += 1

                elif 11 + shiftpoint < iteration < 32 + shiftpoint:
                    # Measures the average amplitude of the impulses
                    # Accounts for the shift at the end of each Buffer
                    if not i:
                        iteration += 1
                        true_bite_average += find_frequency(old_buffer + Buffer[:shift], carrier_frequency, d_sample) / 20
                    elif i == int(d_sample/impulse_length) - 1:
                        old_buffer = Buffer[i * impulse_length + shift:]
                    else:
                        iteration += 1
                        true_bite_average += find_frequency(Buffer[i * impulse_length + shift:impulse_length * (1 + i) + shift], carrier_frequency, d_sample) / 20

                elif iteration == 32 + shiftpoint:
                    # Decides whether the signal represents a 1 ore a 0
                    if not i:
                        bit = find_frequency(old_buffer + Buffer[:shift], carrier_frequency, d_sample)
                    elif i == int(d_sample / impulse_length) - 1:
                        old_buffer = Buffer[i * impulse_length + shift:]
                    else:
                        bit = find_frequency(Buffer[i * impulse_length + shift:impulse_length * (1 + i) + shift], carrier_frequency, d_sample)
                    if bit - true_bite_average > -sensitivity * true_bite_average:
                        wanted_bits += "1"
                    else:
                        wanted_bits += "0"
                    if not initial_sequence:
                        # Looks for the initial binary sequence, which is the Đ character + two correction bytes.
                        if len(wanted_bits) > 23:
                            try:
                                if bytes(get_decoding(wanted_bits[-24:], 1, enc=enc), enc) == bytes("Đ", enc):
                                    initial_sequence = True
                                    wanted_bits = ""
                                else:
                                    pass
                            except:
                                pass
                            if len(wanted_bits) > 180:
                                print("false alarm...")
                                wanted_bits = ""
                                iteration = 10
                                true_bite_average = 0
                                average_buffer = [0, 0, 0]

                    elif initial_sequence and len(wanted_bits) == 32:
                        # Looks for the number which says how many bytes the message has.
                        try:
                            num_bytes = bytes(get_decoding(wanted_bits, 1, enc=enc), enc, 'replace')
                            num_bytes = num_bytes[0] * 256 + num_bytes[1]
                            wanted_bits = ""
                            iteration += 1
                            print("Reading message of " + str(num_bytes-60) + " Bytes.")
                        except:
                            # Reverts back to the stage where increased frequency amplitude is being searched for.
                            print("Failed to receive the length of the message.")
                            iteration = 10
                            average_buffer = [0, 0, 0]
                            true_bite_average = 0
                            wanted_bits = ""
                            initial_sequence = False

                    if not i and not (iteration == 10):
                        # Special case for the first sequence of a Buffer.
                        bit = find_frequency(Buffer[shift:impulse_length + shift], carrier_frequency, d_sample)
                        if bit - true_bite_average > -sensitivity * true_bite_average:
                            wanted_bits += "1"
                        else:
                            wanted_bits += "0"
                        if not initial_sequence:
                            if len(wanted_bits) > 23:
                                try:
                                    if bytes(get_decoding(wanted_bits[-24:], 1, enc=enc), enc) == bytes("Đ", enc):
                                        initial_sequence = True
                                        wanted_bits = ""
                                    else:
                                        pass
                                except:
                                    pass

                        elif initial_sequence and len(wanted_bits) == 32:
                            print(wanted_bits)
                            num_bytes = bytes(get_decoding(wanted_bits, 1, enc=enc), enc, 'replace')
                            num_bytes = num_bytes[0] * 256 + num_bytes[1]
                            wanted_bits = ""
                            iteration += 1

                elif 32 + shiftpoint < iteration < 33 + shiftpoint + 8 * num_bytes:
                    # Looks for the know number of bytes
                    if not i:
                        bit = find_frequency(old_buffer + Buffer[:shift], carrier_frequency, d_sample)
                    elif i == int(d_sample / impulse_length) - 1:
                        old_buffer = Buffer[i * impulse_length + shift:]
                    else:
                        bit = find_frequency(Buffer[i * impulse_length + shift:impulse_length * (1 + i) + shift],
                                             carrier_frequency, d_sample)
                    if bit - true_bite_average > -sensitivity * true_bite_average:
                        wanted_bits += "1"
                    else:
                        wanted_bits += "0"
                    iteration += 1

                elif iteration == 33 + shiftpoint + 8 * num_bytes:
                    # Announces that the transmission of data has successfully been terminated.
                    # performs error-correction on 255 bytes of data at a time.
                    # If unsuccessful the corrupted data is uploaded nonetheless.
                    print("we are done!")
                    for i in range(0,len(wanted_bits) // (255*8)+1):
                        try:
                            message += get_decoding(wanted_bits[255*8*i:255*8*(i + 1)], cushion, enc=enc)
                        except:
                            message += bytearray([(int(wanted_bits[255*8*i:255*8*(i + 1)][:-1 * cushion * 16][k:k + 8], 2)) for k in range(0, len(wanted_bits[255*8*i:255*8*(i + 1)][:-1 * cushion * 16]), 8)]).decode(enc)
                    print("RECEIVED MESSAGE: " + message)

                    # Reverts back to the stage where increased frequency amplitude is being searched for.
                    iteration = 10
                    average_buffer = [0, 0, 0]
                    true_bite_average = 0
                    wanted_bits = ""
                    initial_sequence = False
                    message = ""

            # Skips to a new data in the Buffer
            Buffer = Buffer[buffer_length:]

            if iteration == 10:
                print(".", end="")


thread_listening = myThread()
thread_listening.start()
signal_processing(20700, cushion=30, sensitivity=0.45, impulse_length=49, d_sample=44100, buffer_length=44100, enc='IBM852')
