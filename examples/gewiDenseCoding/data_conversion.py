import binascii


def parse(string, frame_length):
    length = len(string)
    if frame_length > 0 and int(length / frame_length) == length / frame_length:
        number_of_frames = int(length / frame_length)
        frames = []
        for i in range(number_of_frames):
            frames.append(string[i * frame_length: (i + 1) * frame_length])
        return frames
    else:
        return []


# this function parses a bit string into an array of binary letters consisting of two bits each
def parse_message_dense(bits: str):
    # check whether string is of even length ... omitted here
    out = []
    for i in range(int(len(bits) / 2)):
        out.append(bits[2 * i: 2 * i + 2])
    return out


# this function parses a bit string into an array of bits
def parse_message(bits: str):
    # check whether string is of even length ... omitted here
    out = []
    for i in range(int(len(bits))):
        out.append(bits[i: i + 1])
    return out


def int2bytes(i):
    hex_string = '%x' % i
    n = len(hex_string)
    return binascii.unhexlify(hex_string.zfill(n + (n & 1)))


def text_to_bits(text, encoding='utf-8', errors='surrogatepass'):
    bits = bin(int(binascii.hexlify(text.encode(encoding, errors)), 16))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))


def text_from_bits(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return int2bytes(n).decode(encoding, errors)
