from reedsolo import RSCodec


def get_encoding(data, backup_bytes):
    # Uses Reed-Solomon error-correction code to transform a String into ones and zeros which are to be send.

    # data: String of ASCII characters
    # backup_bytes: Number of bits protected against flipping
    # bytes_as_bits: String of ones and zeros

    rsc = RSCodec(2*backup_bytes)
    a = rsc.encode(bytes(data, 'ascii', 'replace'))
    # Unknown characters are replaced with a '?'
    
    bytes_as_bits = ''.join(format(byte, '08b') for byte in a)
    return bytes_as_bits


def get_decoding(data, backup_bytes):
    # Decodes the String of ones and zeros produced by the get_encoding() back into the initial message.
    
    # message: String
    
    rsc = RSCodec(2 * backup_bytes)
    message = rsc.decode(bytearray([(int(data[i:i + 8], 2)) for i in range(0, len(data), 8)]))[0].decode()
    # Cuts data into segments of 8 bits and translates them back into characters
    
    return message
