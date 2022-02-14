import math
import wave
import struct
import vlc
from reedsolo import RSCodec


def save_wav(file_name, audio_data, sample_rate=44100):
    '''Saves audio data into a playable wav file. This method has been chosen because libraries such as sounddevice
    or simpleaudio are for whatever reason not able to reliably play desired output. The speakers crack and frequencies
    above 20kHz can be heard even though they ain't supposed to be.

    # file_name: string, name under which is the sound going to be saved.
    # audio_data: list 1D, collection of audio samples to be saved as wav.
    # sample_rate: integer, self-explanatory.

    # nsamples: integer, overall number of samples in audio_data.'''

    nsamples = len(audio_data)
    wav_file = wave.open(file_name, "w")
    wav_file.setparams((1, 2, sample_rate, nsamples, "NONE", "not compressed"))

    for sample in audio_data:
        wav_file.writeframes(struct.pack('h', int(sample)))

    wav_file.close()

    return


def get_frequency_impulse(frequency, sample_num, amplitude=0.75, sample_rate=44100, convolution_magnitude=2):
    '''Creates an impulse of a given frequency. The edges are smoothed by convolution.

    # frequency: positive integer, interval (20; 20000) can be heard by a human.
    # sample_num: number of created samples, equal to len(data)
    # amplitude: float, 1 being loudest possible, 0 being silence.
    # sample_rate: positive integer, has to be at least two times larger than frequency!
    # convolution_magnitude: positive number, advised interval (1; 10) The smaller the smoother!

    # negligible: float, sets x coordinate at which Gaussian function becomes negligible.
    # 0.0001 being the cutoff magnitude. (Anything smaller is considered negligible.)'''

    negligible = math.log(1 / 0.0001) ** (1 / convolution_magnitude)
    data = []

    for sample in range(sample_num):
        # This loop samples desired sine wave convoluted by Gaussian function.
        data.append(round(32767 * amplitude * math.sin(2 * math.pi * frequency * sample / sample_rate) * math.e ** (
            -abs(negligible * (2 * sample / sample_num - 1)) ** convolution_magnitude), 0))

    return data


def get_encoding(data, backup_bytes, encoding='IBM852'):
    '''Uses Reed-Solomon error-correction code to transform a String into ones and zeros which are to be send.

    # data: String of ASCII characters
    # backup_bytes: Number of bits protected against flipping
    # bytes_as_bits: String of ones and zeros'''

    rsc = RSCodec(2 * backup_bytes)

    if type(data) == type(2):
        # not wasting space for binary numbers
        st = (16 - len(str(bin(data))[2:])) * "0" + str(bin(data))[2:]
        a = rsc.encode(bytearray([int(st[:8], 2), int(st[8:], 2)]))
    else:
        # unknown characters are replaced with a '?'
        a = rsc.encode(bytes(data, encoding, 'replace'))

    bytes_as_bits = ''.join(format(byte, '08b') for byte in a)
    return bytes_as_bits


def Transmit(frequency, chunk_size, convolution_magnitude=2, amplitude=0.75, sample_rate=44100, cushion=30):
    '''THE MAIN FUNCTION used to transmit messages via sound

    # frequency: integer: between 1 and sample_rate/2, frequency on which the data is transmitted
    # chunk_size: integer: length of a frequency impulse in samples.
    # convolution_magnitude: positive number, advised interval (1; 10) The smaller the smoother!
    # amplitude: float, 1 being loudest possible, 0 being silence.
    # sample_rate: positive integer, has to be at least two times larger than frequency!
    # cushion: integer, the number of bytes protected against flipping within each (255 - 2*cushion) bytes.

    # audio_data: list 1D, collection of audio samples to be saved as wav.
    # binary_data: string, Starts off with a compulsory set of impulses, which help the receiver to recognize the signal'''

    while True:
        audio_data = []
        binary_data = "111111111111111111111111111111111111111111111111111111111111111111111111100000000000000000000000"
        message = input("Enter your message: ")

        binary_data += get_encoding("Đ", 1)
        # initial sequence used to recognize the beginning of a transmission.
        binary_data += get_encoding(len(message) + 2*cushion + 2*cushion*(len(message) // (255 - 2*cushion)), 1)
        # length of the message itself and its cushion.
        binary_data += get_encoding(message, cushion)
        # the message itself and its cushion.

        impulse = get_frequency_impulse(frequency, chunk_size, convolution_magnitude=convolution_magnitude, amplitude=amplitude, sample_rate=sample_rate)
        silence = [0.0] * chunk_size

        for i in binary_data:
            if i == "1":
                audio_data += impulse
            else:
                audio_data += silence
                
        audio_data += [0.0]*800
        # Adds some silence at the end of the audio as abrupt end sometimes causes cracking in the speaker.

        save_wav("hovno.wav", audio_data, sample_rate=sample_rate)

        p = vlc.MediaPlayer("hovno.wav")
        p.play()


Transmit(20700, 49, convolution_magnitude=2, amplitude=0.75, sample_rate=44100, cushion=30)
