import math


def discrete_fourier(time_domain):
    # Implements DTFT without a library
    
    frequency_domain = []

    for freq in range(len(time_domain)):
        Sigma = 0
        for sample in range(len(data)):
            Sigma += time_domain[sample] * math.e ** ( -2 * math.pi * freq * sample / len(data) * 1j)
        frequency_domain.append(abs(Sigma))
    # Calculates all samples of the frequency domain
    # The frequency domain has to be interpreted with the initial sample rate in mind. 
    # n-th frequency_domain sample corresponds to the frequency:  n * sample_rate / len(frequency_domain)

    return frequency_domain
