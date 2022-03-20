import math


def get_frequency_impulse(frequency, sample_num, sample_rate=44100, convolution_magnitude=4, delta=0.07):
    # Creates an impulse of a given frequency. The edges are smoothed by convolution.

    # frequency: positive integer, interval (20; 20000) can be heard by a human.
    # sample_num: number of created samples, equal to len(data)
    # sample_rate: positive integer, has to be at least two times larger than frequency!
    # convolution_magnitude: positive number, advised interval (1; 10) The smaller the smoother!

    # delta: the cutoff magnitude of Gaussian function, at which is becomes negligible.
    
    data = []
    for sample in range(sample_num):
        data.append(round(32767 * amplitude * math.sin(2 * math.pi * frequency * sample / sample_rate) * delta ** (
            abs((sample * 2 / sample_num - 1)) ** convolution_magnitude), 0))
    # This loop samples desired sine wave convoluted by Gaussian function.
    
    return data
