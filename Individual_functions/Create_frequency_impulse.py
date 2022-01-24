import math


def get_frequency_impulse(frequency, sample_num, sample_rate=44100, convolution_magnitude=5):
    # Creates an impulse of a given frequency. The edges are smoothed by convolution.

    # frequency: positive integer, interval (20; 20000) can be heard by a human.
    # sample_num: number of created samples, equal to len(data)
    # sample_rate: positive integer, has to be at least two times larger than frequency!
    # convolution_magnitude: positive number, advised interval (1; 10) The smaller the smoother!

    negligible = math.log(1/0.002)**(1 / convolution_magnitude)
    # Sets x coordinate at which Gaussian function becomes negligible.
    # 0.002 being the cutoff magnitude. (Anything smaller is considered negligible.)
    
    data = []
    for sample in range(sample_num):
        data.append(math.sin(2*math.pi * frequency * sample / sample_rate) * math.e ** (-abs(negligible*(2*sample/sample_num - 1)) ** (convolution_magnitude)))
    # This loop samples desired sine wave convoluted by Gaussian function.
    
    return data
