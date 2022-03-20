from reedsolo import RSCodec


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
